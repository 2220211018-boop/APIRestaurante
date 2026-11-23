"""Pruebas del middleware compartido: valida JWT RS256 con la llave pública."""

from datetime import datetime, timedelta, timezone
import jwt
from pruebas_comunes import entorno

PRODUCTO = {
    "nombre": "Tinto",
    "categoria": "Bebidas",
    "precio": 3000.0,
    "descripcion": "Café negro",
}


def intentar(api, token):
    return api.post(
        "/productos/",
        json=PRODUCTO,
        headers={"Authorization": f"Bearer {token}"},
    )


def test_token_valido_de_admin_es_aceptado(api):
    assert intentar(api, entorno.crear_token("ROLE_ADMIN")).status_code == 201


def test_token_firmado_con_otra_llave_privada_es_rechazado(api):
    falso = entorno.crear_token("ROLE_ADMIN", llave=entorno.llave_privada_ajena())
    assert intentar(api, falso).status_code == 401


def test_token_expirado_es_rechazado(api):
    r = intentar(api, entorno.crear_token("ROLE_ADMIN", minutos=-5))
    assert r.status_code == 401
    assert "expirado" in r.json()["detail"]


def test_token_sin_firma_algoritmo_none_es_rechazado(api):
    carga = {
        "sub": "1",
        "rol": "ROLE_ADMIN",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    sin_firma = jwt.encode(carga, "", algorithm="none")
    assert intentar(api, sin_firma).status_code == 401


def test_token_sin_rol_es_rechazado(api):
    carga = {
        "sub": "1",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    incompleto = jwt.encode(carga, entorno.LLAVE_PRIVADA, algorithm="RS256")
    assert intentar(api, incompleto).status_code == 401


def test_token_corrupto_es_rechazado(api):
    assert intentar(api, "esto.no.es-un-jwt").status_code == 401