import jwt
from pruebas_comunes import entorno

USUARIO = {
    "nombre_completo": "Ana Pérez",
    "correo": "ana@correo.com",
    "contrasena": "Clave123",
}
CREDENCIALES = {
    "correo": USUARIO["correo"],
    "contrasena": USUARIO["contrasena"],
}


def registrar(api, datos=None):
    return api.post("/auth/registro", json=datos or USUARIO)


def iniciar_sesion(api):
    registrar(api)
    return api.post("/auth/login", json=CREDENCIALES).json()["access_token"]


# --- Registro ---


def test_registro_exitoso_asigna_rol_usuario(api):
    r = registrar(api)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["correo"] == USUARIO["correo"]
    assert cuerpo["rol"] == "ROLE_USER"
    assert "contrasena" not in cuerpo and "contrasena_hash" not in cuerpo


def test_correo_configurado_como_admin_recibe_rol_admin(api):
    r = registrar(api, {**USUARIO, "correo": "admin@restaurante.com"})
    assert r.json()["rol"] == "ROLE_ADMIN"


def test_registro_con_correo_repetido_falla(api):
    registrar(api)
    r = registrar(api)
    assert r.status_code == 400


def test_registro_con_contrasena_corta_falla(api):
    r = registrar(api, {**USUARIO, "contrasena": "123"})
    assert r.status_code == 422


def test_la_contrasena_se_guarda_con_hash_bcrypt(api):
    from rutas import rutas_auth

    registrar(api)
    guardado = rutas_auth.base_datos_usuarios[0]["contrasena_hash"]
    assert guardado != USUARIO["contrasena"]
    assert guardado.startswith("$2")  # prefijo de bcrypt


# --- Login y JWT RS256 ---


def test_login_devuelve_jwt_firmado_con_rs256(api):
    token = iniciar_sesion(api)
    assert jwt.get_unverified_header(token)["alg"] == "RS256"
    # Se valida con la llave PÚBLICA (la privada solo la tiene este servicio)
    datos = jwt.decode(token, entorno.LLAVE_PUBLICA, algorithms=["RS256"])
    assert datos["correo"] == USUARIO["correo"]
    assert datos["rol"] == "ROLE_USER"
    assert "exp" in datos


def test_login_con_contrasena_incorrecta_falla(api):
    registrar(api)
    r = api.post("/auth/login", json={**CREDENCIALES, "contrasena": "otra-clave"})
    assert r.status_code == 401


def test_login_con_usuario_inexistente_falla(api):
    r = api.post("/auth/login", json=CREDENCIALES)
    assert r.status_code == 401


# --- OAuth 2.0 (flujo Password) ---


def test_oauth2_token_entrega_access_token_bearer(api):
    registrar(api)
    r = api.post(
        "/auth/token",
        data={"username": USUARIO["correo"], "password": USUARIO["contrasena"]},
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["token_type"] == "bearer"
    jwt.decode(cuerpo["access_token"], entorno.LLAVE_PUBLICA, algorithms=["RS256"])


def test_oauth2_token_con_credenciales_invalidas(api):
    r = api.post(
        "/auth/token",
        data={"username": "nadie@correo.com", "password": "xxxxxx"},
    )
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"


# --- Perfil protegido ---


def test_perfil_con_token_valido(api):
    token = iniciar_sesion(api)
    r = api.get("/auth/perfil", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["correo"] == USUARIO["correo"]


def test_perfil_sin_token_es_rechazado(api):
    assert api.get("/auth/perfil").status_code in (401, 403)


def test_perfil_con_token_firmado_con_otra_llave(api):
    registrar(api)
    falso = entorno.crear_token(correo=USUARIO["correo"], llave=entorno.llave_privada_ajena())
    r = api.get("/auth/perfil", headers={"Authorization": f"Bearer {falso}"})
    assert r.status_code == 401


def test_perfil_con_token_expirado(api):
    registrar(api)
    vencido = entorno.crear_token(correo=USUARIO["correo"], minutos=-5)
    r = api.get("/auth/perfil", headers={"Authorization": f"Bearer {vencido}"})
    assert r.status_code == 401