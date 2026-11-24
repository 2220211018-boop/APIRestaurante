import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pruebas_comunes import entorno

# Preparar el entorno antes de importar el servicio.
entorno.preparar("servicio_inventario")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def api():
    import principal
    from base_datos import SessionLocal
    from modelos.tablas import InventarioTabla

    # Limpiar los registros antes de cada prueba.
    db = SessionLocal()
    try:
        db.query(InventarioTabla).delete()
        db.commit()
    finally:
        db.close()

    return TestClient(principal.app)


@pytest.fixture()
def usuario():
    return entorno.cabecera("ROLE_USER", "2")


@pytest.fixture()
def admin():
    return entorno.cabecera("ROLE_ADMIN", "1")