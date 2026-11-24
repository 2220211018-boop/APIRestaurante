import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pruebas_comunes import entorno

entorno.preparar("servicio_pagos_domicilios")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def api():
    import principal
    from rutas import rutas_domicilio, rutas_pago

    # Limpiar los registros antes de cada prueba
    rutas_pago.base_datos_pagos.clear()
    rutas_domicilio.base_datos_domicilios.clear()

    return TestClient(principal.app)


@pytest.fixture()
def usuario():
    return entorno.cabecera("ROLE_USER", "2")