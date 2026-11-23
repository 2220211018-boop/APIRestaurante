CAPUCHINO = {
    "nombre": "Café Capuchino",
    "categoria": "Bebidas Calientes",
    "precio": 8500.0,
    "descripcion": "Café expreso con leche vaporizada",
    "disponible": True,
}
EMPANADA = {
    **CAPUCHINO,
    "nombre": "Empanada",
    "categoria": "Comidas",
    "precio": 2500.0,
}


def crear(api, admin, datos=CAPUCHINO):
    r = api.post("/productos/", json=datos, headers=admin)
    assert r.status_code == 201
    return r.json()["producto"]


def test_inicio_del_servicio(api):
    assert api.get("/").status_code == 200


def test_listar_productos_vacio_es_publico(api):
    r = api.get("/productos/")
    assert r.status_code == 200
    assert r.json() == []


def test_crear_producto_sin_token_es_rechazado(api):
    assert api.post("/productos/", json=CAPUCHINO).status_code in (401, 403)


def test_crear_producto_como_usuario_normal_da_403(api, usuario):
    assert api.post("/productos/", json=CAPUCHINO, headers=usuario).status_code == 403


def test_crear_producto_como_admin(api, admin):
    r = api.post("/productos/", json=CAPUCHINO, headers=admin)
    assert r.status_code == 201
    producto = r.json()["producto"]
    assert producto["id"] >= 1
    assert producto["nombre"] == "Café Capuchino"
    assert producto["precio"] == 8500.0


def test_no_permite_productos_duplicados(api, admin):
    crear(api, admin)
    r = api.post("/productos/", json=CAPUCHINO, headers=admin)
    assert r.status_code == 400


def test_listar_incluye_productos_creados(api, admin):
    crear(api, admin)
    crear(api, admin, EMPANADA)
    assert len(api.get("/productos/").json()) == 2


def test_obtener_producto_por_id(api, admin):
    producto = crear(api, admin)
    r = api.get(f"/productos/{producto['id']}")
    assert r.status_code == 200
    assert r.json()["nombre"] == "Café Capuchino"


def test_obtener_producto_inexistente_da_404(api):
    assert api.get("/productos/999").status_code == 404


def test_actualizar_producto(api, admin):
    producto = crear(api, admin)
    r = api.put(
        f"/productos/{producto['id']}",
        json={**CAPUCHINO, "precio": 9000.0},
        headers=admin,
    )
    assert r.status_code == 200
    assert api.get(f"/productos/{producto['id']}").json()["precio"] == 9000.0


def test_actualizar_producto_inexistente_da_404(api, admin):
    assert api.put("/productos/999", json=CAPUCHINO, headers=admin).status_code == 404


def test_actualizar_con_nombre_de_otro_producto_falla(api, admin):
    crear(api, admin)
    otro = crear(api, admin, EMPANADA)
    r = api.put(f"/productos/{otro['id']}", json=CAPUCHINO, headers=admin)
    assert r.status_code == 400


def test_usuario_normal_no_puede_actualizar_ni_borrar(api, admin, usuario):
    producto = crear(api, admin)
    assert api.put(f"/productos/{producto['id']}", json=CAPUCHINO, headers=usuario).status_code == 403
    assert api.delete(f"/productos/{producto['id']}", headers=usuario).status_code == 403


def test_eliminar_producto(api, admin):
    producto = crear(api, admin)
    assert api.delete(f"/productos/{producto['id']}", headers=admin).status_code == 200
    assert api.get(f"/productos/{producto['id']}").status_code == 404


def test_eliminar_producto_inexistente_da_404(api, admin):
    assert api.delete("/productos/999", headers=admin).status_code == 404