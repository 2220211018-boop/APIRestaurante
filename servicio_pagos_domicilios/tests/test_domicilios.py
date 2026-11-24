DOMICILIO = {
    "id_pedido": "PED-1",
    "direccion_entrega": "Calle 10 # 5-20",
    "nombre_repartidor": "Juan Pérez",
}


def test_listar_domicilios_sin_token_es_rechazado(api):
    respuesta = api.get("/domicilios/")
    assert respuesta.status_code in (401, 403)


def test_crear_domicilio_sin_token_es_rechazado(api):
    respuesta = api.post("/domicilios/", json=DOMICILIO)
    assert respuesta.status_code in (401, 403)


def test_crear_domicilio_con_token_valido(api, usuario):
    respuesta = api.post(
        "/domicilios/",
        json=DOMICILIO,
        headers=usuario,
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["id"] == "1"
    assert cuerpo["datos"]["nombre_repartidor"] == "Juan Pérez"
    assert cuerpo["datos"]["estado_envio"] == "EN CAMINO"


def test_domicilio_incompleto_da_422(api, usuario):
    respuesta = api.post(
        "/domicilios/",
        json={"id_pedido": "PED-1"},
        headers=usuario,
    )
    assert respuesta.status_code == 422


def test_listar_domicilios_devuelve_los_registrados(api, usuario):
    api.post("/domicilios/", json=DOMICILIO, headers=usuario)

    respuesta = api.get("/domicilios/", headers=usuario)

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 1