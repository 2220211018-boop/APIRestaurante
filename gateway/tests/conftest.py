import os
import sys
from pathlib import Path

# El gateway no usa JWT ni base de datos: solo necesita sus URLs y `main`.
os.environ["URL_AUTH"] = "http://auth-falso:8000"
os.environ["URL_CLIENTES_PRODUCTOS"] = "http://productos-falso:8000"
os.environ["URL_PAGOS_DOMICILIOS"] = "http://pagos-falso:8000"
os.environ["URL_PEDIDOS"] = "http://pedidos-falso:8000"
os.environ["URL_INVENTARIO"] = "http://inventario-falso:8000"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
import pytest
from fastapi.testclient import TestClient


class RespuestaFalsa:
    status_code = 200
    content = b'{"ok": true}'
    headers = {"content-type": "application/json"}


class MicroservicioFalso:
    """Reemplaza a httpx.AsyncClient: guarda las llamadas y responde sin usar la red."""

    llamadas = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def request(self, method, url, headers, params, content):
        MicroservicioFalso.llamadas.append({"method": method, "url": url, "headers": headers})
        return RespuestaFalsa()


class MicroservicioCaido(MicroservicioFalso):
    async def request(self, method, url, headers, params, content):
        raise httpx.ConnectError("conexión rechazada (simulada)")


@pytest.fixture()
def api():
    import main

    MicroservicioFalso.llamadas.clear()
    return TestClient(main.app)


@pytest.fixture()
def con_microservicio(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", MicroservicioFalso)
    return MicroservicioFalso


@pytest.fixture()
def con_microservicio_caido(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", MicroservicioCaido)
