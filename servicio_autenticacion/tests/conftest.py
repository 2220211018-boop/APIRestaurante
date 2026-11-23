import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pruebas_comunes import entorno

entorno.preparar("servicio_autenticacion", ADMIN_EMAIL="admin@restaurante.com")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def api():
    import principal
    from rutas import rutas_auth

    rutas_auth.base_datos_usuarios.clear()  # los usuarios viven en memoria
    return TestClient(principal.app)