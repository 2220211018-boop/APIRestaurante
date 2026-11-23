def test_inicio_lista_los_servicios(api):
    r = api.get("/")
    assert r.status_code == 200
    servicios = r.json()["servicios"]
    for nombre in ("auth", "clientes", "productos", "pagos", "domicilios", "pedidos", "inventario"):
        assert nombre in servicios


def test_servicio_inexistente_devuelve_404(api):
    r = api.get("/api/noexiste/")
    assert r.status_code == 404
    assert "noexiste" in r.json()["detail"]


def test_reenvia_la_peticion_al_microservicio_correcto(api, con_microservicio):
    r = api.get("/api/productos/")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    assert con_microservicio.llamadas[0]["url"] == "http://productos-falso:8000/productos/"


def test_reenvia_rutas_con_subruta(api, con_microservicio):
    api.get("/api/pedidos/5")
    assert con_microservicio.llamadas[0]["url"] == "http://pedidos-falso:8000/pedidos/5"


def test_reenvia_el_token_jwt_sin_modificarlo(api, con_microservicio):
    api.get("/api/inventario/alertas", headers={"Authorization": "Bearer abc.def.ghi"})
    assert con_microservicio.llamadas[0]["headers"]["authorization"] == "Bearer abc.def.ghi"


def test_genera_id_de_correlacion_si_no_viene(api, con_microservicio):
    r = api.get("/api/productos/")
    assert r.headers["x-correlation-id"]


def test_respeta_el_id_de_correlacion_recibido(api, con_microservicio):
    r = api.get("/api/productos/", headers={"X-Correlation-Id": "abc-123"})
    assert r.headers["x-correlation-id"] == "abc-123"
    assert con_microservicio.llamadas[0]["headers"]["X-Correlation-Id"] == "abc-123"


def test_microservicio_caido_devuelve_503(api, con_microservicio_caido):
    r = api.get("/api/auth/perfil")
    assert r.status_code == 503
    assert "no está disponible" in r.json()["detail"]
    assert r.headers["x-correlation-id"]
