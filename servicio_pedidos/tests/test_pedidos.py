import pytest
from fastapi import HTTPException

from rutas import rutas_pedido


DATOS_PEDIDO = {
    "direccion_entrega": "Calle 10 # 5-20, Ibagué",
    "items": [{"producto_id": 1, "cantidad": 2}],
}


def producto_disponible(producto_id):
    return {
        "disponible": True,
        "nombre": "Producto de prueba",
        "precio": 10.0,
    }


def sin_error_inventario(accion, items, authorization):
    return None


def crear_pedido(api, cabecera):
    return api.post(
        "/pedidos/",
        json=DATOS_PEDIDO,
        headers=cabecera,
    )


def preparar_servicios(monkeypatch):
    monkeypatch.setattr(
        rutas_pedido, "consultar_producto", producto_disponible
    )
    monkeypatch.setattr(
        rutas_pedido, "mover_inventario", sin_error_inventario
    )


def test_inicio_del_servicio(api):
    respuesta = api.get("/")
    assert respuesta.status_code == 200


def test_listar_pedidos_sin_token_es_rechazado(api):
    respuesta = api.get("/pedidos/")
    assert respuesta.status_code in (401, 403)


def test_obtener_pedido_sin_token_es_rechazado(api):
    respuesta = api.get("/pedidos/1")
    assert respuesta.status_code in (401, 403)


def test_crear_pedido_sin_token_es_rechazado(api):
    respuesta = api.post("/pedidos/", json=DATOS_PEDIDO)
    assert respuesta.status_code in (401, 403)


def test_actualizar_pedido_sin_rol_admin_es_rechazado(api, usuario):
    respuesta = api.put(
        "/pedidos/1",
        json={"estado": "EN_PREPARACION"},
        headers=usuario,
    )
    assert respuesta.status_code == 403


def test_eliminar_pedido_sin_rol_admin_es_rechazado(api, usuario):
    respuesta = api.delete("/pedidos/1", headers=usuario)
    assert respuesta.status_code == 403


def test_crear_pedido_con_token_valido(api, usuario, monkeypatch):
    preparar_servicios(monkeypatch)

    respuesta = crear_pedido(api, usuario)

    assert respuesta.status_code == 201
    datos = respuesta.json()["pedido"]
    assert datos["usuario_id"] == "2"
    assert datos["estado"] == "PENDIENTE"
    assert datos["total"] == 20.0
    assert datos["items"][0]["producto_id"] == 1


def test_pedido_sin_items_es_rechazado(api, usuario, monkeypatch):
    preparar_servicios(monkeypatch)

    respuesta = api.post(
        "/pedidos/",
        json={"direccion_entrega": "Calle 10", "items": []},
        headers=usuario,
    )

    assert respuesta.status_code == 400


def test_pedido_con_cantidad_cero_es_rechazado(api, usuario, monkeypatch):
    preparar_servicios(monkeypatch)

    respuesta = api.post(
        "/pedidos/",
        json={
            "direccion_entrega": "Calle 10",
            "items": [{"producto_id": 1, "cantidad": 0}],
        },
        headers=usuario,
    )

    assert respuesta.status_code == 422


def test_producto_no_disponible_rechaza_pedido(api, usuario, monkeypatch):
    monkeypatch.setattr(
        rutas_pedido,
        "consultar_producto",
        lambda producto_id: {
            "disponible": False,
            "nombre": "Producto agotado",
            "precio": 10.0,
        },
    )
    monkeypatch.setattr(
        rutas_pedido, "mover_inventario", sin_error_inventario
    )

    respuesta = crear_pedido(api, usuario)

    assert respuesta.status_code == 400


def test_error_de_productos_devuelve_503(api, usuario, monkeypatch):
    def producto_no_disponible(producto_id):
        raise HTTPException(status_code=503, detail="Servicio no disponible")

    monkeypatch.setattr(
        rutas_pedido, "consultar_producto", producto_no_disponible
    )

    respuesta = crear_pedido(api, usuario)

    assert respuesta.status_code == 503


def test_falta_de_inventario_devuelve_409(api, usuario, monkeypatch):
    monkeypatch.setattr(
        rutas_pedido, "consultar_producto", producto_disponible
    )

    def inventario_insuficiente(accion, items, authorization):
        raise HTTPException(status_code=409, detail="Stock insuficiente")

    monkeypatch.setattr(
        rutas_pedido, "mover_inventario", inventario_insuficiente
    )

    respuesta = crear_pedido(api, usuario)

    assert respuesta.status_code == 409


def test_usuario_solo_lista_sus_pedidos(api, usuario, monkeypatch):
    preparar_servicios(monkeypatch)
    crear_pedido(api, usuario)
    otro_usuario = {"Authorization": usuario["Authorization"]}
    otro_usuario["Authorization"] = (
        "Bearer " + __import__("pruebas_comunes").entorno.crear_token(
            rol="ROLE_USER", sub="3"
        )
    )
    crear_pedido(api, otro_usuario)

    respuesta = api.get("/pedidos/", headers=usuario)

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 1
    assert respuesta.json()[0]["usuario_id"] == "2"


def test_usuario_no_puede_ver_pedido_de_otro(api, usuario, monkeypatch):
    preparar_servicios(monkeypatch)
    otro_usuario = {
        "Authorization": "Bearer "
        + __import__("pruebas_comunes").entorno.crear_token(
            rol="ROLE_USER", sub="3"
        )
    }
    creado = crear_pedido(api, otro_usuario)
    pedido_id = creado.json()["pedido"]["id"]

    respuesta = api.get(f"/pedidos/{pedido_id}", headers=usuario)

    assert respuesta.status_code == 403


def test_admin_actualiza_estado_del_pedido(api, usuario, admin, monkeypatch):
    preparar_servicios(monkeypatch)
    creado = crear_pedido(api, usuario)
    pedido_id = creado.json()["pedido"]["id"]

    respuesta = api.put(
        f"/pedidos/{pedido_id}",
        json={"estado": "EN_PREPARACION"},
        headers=admin,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["pedido"]["estado"] == "EN_PREPARACION"