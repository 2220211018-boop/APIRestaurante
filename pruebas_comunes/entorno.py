"""Utilidades compartidas por las pruebas de todos los microservicios.

Qué hace:
  * Genera un par de llaves RSA temporal (las pruebas NO usan private_key.pem real).
  * Configura las variables de entorno que leen los servicios (llaves y DATABASE_URL
    apuntando a SQLite), de modo que las pruebas no necesitan PostgreSQL ni Docker.
  * Crea tokens JWT RS256 de prueba (usuario, admin, expirado, con otra llave...).

IMPORTANTE: preparar() debe llamarse en el conftest.py ANTES de importar el servicio.
"""
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

RAIZ = Path(__file__).resolve().parents[1]
CARPETA = Path(tempfile.mkdtemp(prefix="pruebas_restaurante_"))


def _generar_par_de_llaves():
    clave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    privada = clave.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    publica = clave.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return privada, publica


LLAVE_PRIVADA, LLAVE_PUBLICA = _generar_par_de_llaves()


def llave_privada_ajena() -> bytes:
    """Otra llave privada distinta: sirve para probar que se rechazan firmas falsas."""
    return _generar_par_de_llaves()[0]


def preparar(servicio: str, **variables_de_entorno) -> None:
    """Configura entorno y rutas de importación para probar `servicio`."""
    (CARPETA / "private_key.pem").write_bytes(LLAVE_PRIVADA)
    (CARPETA / "public_key.pem").write_bytes(LLAVE_PUBLICA)
    os.environ["PRIVATE_KEY_PATH"] = str(CARPETA / "private_key.pem")
    os.environ["PUBLIC_KEY_PATH"] = str(CARPETA / "public_key.pem")
    os.environ["DATABASE_URL"] = "sqlite:///" + (CARPETA / "prueba.db").as_posix()
    for nombre, valor in variables_de_entorno.items():
        os.environ[nombre] = valor

    # La carpeta del servicio va primero (import principal, rutas, modelos...);
    # la raíz permite importar `shared` igual que dentro del contenedor.
    for ruta in (RAIZ, RAIZ / servicio):
        if str(ruta) not in sys.path:
            sys.path.insert(0, str(ruta))


def crear_token(rol="ROLE_USER", sub="1", correo="usuario@prueba.com",
                minutos=60, llave=None) -> str:
    carga = {
        "sub": sub,
        "correo": correo,
        "rol": rol,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=minutos),
    }
    return jwt.encode(carga, llave or LLAVE_PRIVADA, algorithm="RS256")


def cabecera(rol="ROLE_USER", sub="1", **opciones) -> dict:
    """Cabecera `Authorization: Bearer <jwt>` lista para usar en las pruebas."""
    return {"Authorization": f"Bearer {crear_token(rol, sub, **opciones)}"}
