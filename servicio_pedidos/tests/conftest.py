import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pruebas_comunes import entorno

# Debe ejecutarse antes de importar el servicio.
entorno.preparar("servicio_pedidos")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def api():
    import principal
    from base_datos import SessionLocal
    from modelos.tablas import ItemPedidoTabla, PedidoTabla

    # Limpiar los datos de prueba antes de cada test.
    db = SessionLocal()
    try:
        db.query(ItemPedidoTabla).delete()
        db.query(PedidoTabla).delete()
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