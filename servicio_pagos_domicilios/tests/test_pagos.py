PAGO = {
    "id_pedido": "PED-1",
    "monto": 8500.0,
    "metodo_pago": "NEQUI",
}


def test_inicio_del_servicio(api):
    assert api.get("/").status_code == 200


def test_listar_pagos_sin_token_es_rechazado(api):
    assert api.get("/pagos/").status_code in (401, 403)


def test_crear_pago_sin_token_es_rechazado(api):
    assert api.post("/pagos/", json=PAGO).status_code in (401, 403)


def test_crear_pago_con_token_valido(api, usuario):
    respuesta = api.post("/pagos/", json=PAGO, headers=usuario)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["id"] == "1"
    assert cuerpo["datos"]["monto"] == 8500.0
    assert cuerpo["datos"]["estado"] == "COMPLETADO"


def test_pago_incompleto_da_422(api, usuario):
    respuesta = api.post(
        "/pagos/",
        json={"id_pedido": "PED-1"},
        headers=usuario,
    )
    assert respuesta.status_code == 422


def test_listar_pagos_devuelve_los_registrados(api, usuario):
    api.post("/pagos/", json=PAGO, headers=usuario)
    api.post(
        "/pagos/",
        json={**PAGO, "id_pedido": "PED-2"},
        headers=usuario,
    )

    respuesta = api.get("/pagos/", headers=usuario)

    assert respuesta.status_code == 200
    assert [pago["id_pedido"] for pago in respuesta.json()] == ["PED-1", "PED-2"]