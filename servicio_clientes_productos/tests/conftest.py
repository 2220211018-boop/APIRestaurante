import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pruebas_comunes import entorno

entorno.preparar("servicio_clientes_productos")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def base_de_datos_limpia():
    import principal  # al importarlo crea las tablas
    from base_datos import Base, engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture()
def api():
    import principal

    return TestClient(principal.app)


@pytest.fixture()
def admin():
    return entorno.cabecera("ROLE_ADMIN", "1")


@pytest.fixture()
def usuario():
    return entorno.cabecera("ROLE_USER", "2")