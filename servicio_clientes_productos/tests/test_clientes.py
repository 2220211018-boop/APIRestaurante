CARLOS = {
    "nombre_completo": "Carlos Mendoza",
    "correo": "carlos@gmail.com",
    "telefono": "3001234567",
    "direccion": "Calle 10 # 5-20",
}
MARIA = {
    **CARLOS,
    "nombre_completo": "María Gómez",
    "correo": "maria@gmail.com",
}


def crear(api, admin, datos=CARLOS):
    r = api.post("/clientes/", json=datos, headers=admin)
    assert r.status_code == 201
    return r.json()["cliente"]


def test_crear_cliente_como_admin(api, admin):
    r = api.post("/clientes/", json=CARLOS, headers=admin)
    assert r.status_code == 201
    assert r.json()["cliente"]["correo"] == "carlos@gmail.com"


def test_crear_cliente_como_usuario_normal_da_403(api, usuario):
    assert api.post("/clientes/", json=CARLOS, headers=usuario).status_code == 403


def test_crear_cliente_sin_token_es_rechazado(api):
    assert api.post("/clientes/", json=CARLOS).status_code in (401, 403)


def test_no_permite_correo_repetido(api, admin):
    crear(api, admin)
    assert api.post("/clientes/", json=CARLOS, headers=admin).status_code == 400


def test_listar_y_obtener_cliente(api, admin):
    cliente = crear(api, admin)
    crear(api, admin, MARIA)
    assert len(api.get("/clientes/").json()) == 2
    r = api.get(f"/clientes/{cliente['id']}")
    assert r.status_code == 200
    assert r.json()["nombre"] == "Carlos Mendoza"


def test_obtener_cliente_inexistente_da_404(api):
    assert api.get("/clientes/999").status_code == 404


def test_actualizar_cliente(api, admin):
    cliente = crear(api, admin)
    r = api.put(
        f"/clientes/{cliente['id']}",
        json={**CARLOS, "telefono": "3109999999"},
        headers=admin,
    )
    assert r.status_code == 200
    assert api.get(f"/clientes/{cliente['id']}").json()["telefono"] == "3109999999"


def test_actualizar_con_correo_de_otro_cliente_falla(api, admin):
    crear(api, admin)
    maria = crear(api, admin, MARIA)
    r = api.put(
        f"/clientes/{maria['id']}",
        json={**MARIA, "correo": CARLOS["correo"]},
        headers=admin,
    )
    assert r.status_code == 400


def test_eliminar_cliente(api, admin):
    cliente = crear(api, admin)
    assert api.delete(f"/clientes/{cliente['id']}", headers=admin).status_code == 200
    assert api.get(f"/clientes/{cliente['id']}").status_code == 404


def test_eliminar_cliente_inexistente_da_404(api, admin):
    assert api.delete("/clientes/999", headers=admin).status_code == 404