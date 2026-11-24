from fastapi import HTTPException

from rutas import rutas_inventario


def registrar(api, admin, monkeypatch, producto_id=1, stock=10, stock_minimo=3):
    monkeypatch.setattr(
        rutas_inventario,
        "verificar_producto_existe",
        lambda _: None,
    )

    return api.post(
        "/inventario/",
        json={
            "producto_id": producto_id,
            "stock": stock,
            "stock_minimo": stock_minimo,
        },
        headers=admin,
    )


def test_inicio_servicio(api):
    respuesta = api.get("/")

    assert respuesta.status_code == 200
    assert "mensaje" in respuesta.json()


def test_listar_inventario_usuario_no_autorizado(api, usuario):
    respuesta = api.get("/inventario/", headers=usuario)

    assert respuesta.status_code == 403


def test_listar_inventario_admin(api, admin):
    respuesta = api.get("/inventario/", headers=admin)

    assert respuesta.status_code == 200
    assert isinstance(respuesta.json(), list)


def test_alertas_usuario_no_autorizado(api, usuario):
    respuesta = api.get("/inventario/alertas", headers=usuario)

    assert respuesta.status_code == 403


def test_crear_inventario_usuario_no_autorizado(api, usuario):
    respuesta = api.post(
        "/inventario/",
        json={"producto_id": 1, "stock": 10, "stock_minimo": 3},
        headers=usuario,
    )

    assert respuesta.status_code == 403


def test_crear_inventario_correctamente(api, admin, monkeypatch):
    respuesta = registrar(api, admin, monkeypatch)

    assert respuesta.status_code == 201
    assert respuesta.json()["inventario"]["producto_id"] == 1
    assert respuesta.json()["inventario"]["stock"] == 10


def test_crear_inventario_producto_inexistente(api, admin, monkeypatch):
    def producto_inexistente(_):
        raise HTTPException(status_code=400, detail="Producto inexistente")

    monkeypatch.setattr(
        rutas_inventario,
        "verificar_producto_existe",
        producto_inexistente,
    )

    respuesta = api.post(
        "/inventario/",
        json={"producto_id": 99, "stock": 10, "stock_minimo": 3},
        headers=admin,
    )

    assert respuesta.status_code == 400


def test_no_permitir_producto_duplicado(api, admin, monkeypatch):
    primera = registrar(api, admin, monkeypatch)
    segunda = registrar(api, admin, monkeypatch)

    assert primera.status_code == 201
    assert segunda.status_code == 400


def test_no_permitir_stock_negativo(api, admin, monkeypatch):
    monkeypatch.setattr(
        rutas_inventario,
        "verificar_producto_existe",
        lambda _: None,
    )

    respuesta = api.post(
        "/inventario/",
        json={"producto_id": 1, "stock": -1, "stock_minimo": 3},
        headers=admin,
    )

    assert respuesta.status_code == 422


def test_consultar_stock_existente(api, admin, usuario, monkeypatch):
    registrar(api, admin, monkeypatch)

    respuesta = api.get("/inventario/1", headers=usuario)

    assert respuesta.status_code == 200
    assert respuesta.json()["producto_id"] == 1
    assert respuesta.json()["stock"] == 10
    assert respuesta.json()["bajo_minimo"] is False


def test_consultar_stock_inexistente(api, usuario):
    respuesta = api.get("/inventario/99", headers=usuario)

    assert respuesta.status_code == 404


def test_actualizar_inventario_usuario_no_autorizado(
    api, admin, usuario, monkeypatch
):
    registrar(api, admin, monkeypatch)

    respuesta = api.put(
        "/inventario/1",
        json={"stock": 20, "stock_minimo": 5},
        headers=usuario,
    )

    assert respuesta.status_code == 403


def test_actualizar_inventario_correctamente(api, admin, monkeypatch):
    registrar(api, admin, monkeypatch)

    respuesta = api.put(
        "/inventario/1",
        json={"stock": 20, "stock_minimo": 5},
        headers=admin,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["inventario"]["stock"] == 20
    assert respuesta.json()["inventario"]["stock_minimo"] == 5


def test_eliminar_inventario_usuario_no_autorizado(
    api, admin, usuario, monkeypatch
):
    registrar(api, admin, monkeypatch)

    respuesta = api.delete("/inventario/1", headers=usuario)

    assert respuesta.status_code == 403


def test_eliminar_inventario_correctamente(api, admin, monkeypatch):
    registrar(api, admin, monkeypatch)

    respuesta = api.delete("/inventario/1", headers=admin)

    assert respuesta.status_code == 200


def test_eliminar_inventario_inexistente(api, admin):
    respuesta = api.delete("/inventario/99", headers=admin)

    assert respuesta.status_code == 404


def test_obtener_alertas_de_stock_bajo(api, admin, monkeypatch):
    registrar(api, admin, monkeypatch, producto_id=1, stock=2, stock_minimo=3)
    registrar(api, admin, monkeypatch, producto_id=2, stock=10, stock_minimo=3)

    respuesta = api.get("/inventario/alertas", headers=admin)

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 1
    assert respuesta.json()[0]["producto_id"] == 1


def test_descontar_inventario_sin_autenticacion(api):
    respuesta = api.post(
        "/inventario/descontar",
        json={"items": [{"producto_id": 1, "cantidad": 1}]},
    )

    assert respuesta.status_code in (401, 403)


def test_descontar_stock_insuficiente_no_modifica_inventario(
    api, admin, usuario, monkeypatch
):
    registrar(api, admin, monkeypatch, producto_id=1, stock=5)
    registrar(api, admin, monkeypatch, producto_id=2, stock=1)

    respuesta = api.post(
        "/inventario/descontar",
        json={
            "items": [
                {"producto_id": 1, "cantidad": 2},
                {"producto_id": 2, "cantidad": 3},
            ]
        },
        headers=usuario,
    )

    assert respuesta.status_code == 409

    consulta = api.get("/inventario/1", headers=usuario)
    assert consulta.status_code == 200
    assert consulta.json()["stock"] == 5


def test_descontar_inventario_correctamente_y_agrupar_items(
    api, admin, usuario, monkeypatch
):
    registrar(api, admin, monkeypatch, producto_id=1, stock=10)

    respuesta = api.post(
        "/inventario/descontar",
        json={
            "items": [
                {"producto_id": 1, "cantidad": 2},
                {"producto_id": 1, "cantidad": 3},
            ]
        },
        headers=usuario,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["productos"] == [1]

    consulta = api.get("/inventario/1", headers=usuario)
    assert consulta.json()["stock"] == 5


def test_reponer_inventario_usuario_no_autorizado(
    api, admin, usuario, monkeypatch
):
    registrar(api, admin, monkeypatch)

    respuesta = api.post(
        "/inventario/reponer",
        json={"items": [{"producto_id": 1, "cantidad": 2}]},
        headers=usuario,
    )

    assert respuesta.status_code == 403


def test_reponer_inventario_correctamente_y_agrupar_items(
    api, admin, monkeypatch
):
    registrar(api, admin, monkeypatch, producto_id=1, stock=5)

    respuesta = api.post(
        "/inventario/reponer",
        json={
            "items": [
                {"producto_id": 1, "cantidad": 2},
                {"producto_id": 1, "cantidad": 3},
            ]
        },
        headers=admin,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["productos"] == [1]

    consulta = api.get("/inventario/1", headers=admin)
    assert consulta.json()["stock"] == 10