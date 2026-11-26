
import os
import uuid

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI(title="API Gateway - Restaurante y Cafetería")

SERVICIOS = {
    "auth": (os.getenv("URL_AUTH", "http://servicio_autenticacion:8000"), "/auth"),
    "clientes": (os.getenv("URL_CLIENTES_PRODUCTOS", "http://servicio_clientes_productos:8000"), "/clientes"),
    "productos": (os.getenv("URL_CLIENTES_PRODUCTOS", "http://servicio_clientes_productos:8000"), "/productos"),
    "pagos": (os.getenv("URL_PAGOS_DOMICILIOS", "http://servicio_pagos_domicilios:8000"), "/pagos"),
    "pedidos": (os.getenv("URL_PEDIDOS", "http://servicio_pedidos:8000"), "/pedidos"),
    "inventario": (os.getenv("URL_INVENTARIO", "http://servicio_inventario:8000"), "/inventario"),
    "domicilios": (os.getenv("URL_PAGOS_DOMICILIOS", "http://servicio_pagos_domicilios:8000"), "/domicilios"),
}

CABECERAS_IGNORADAS = {
    "host",
    "content-length",
    "content-encoding",
    "transfer-encoding",
    "connection",
}

@app.get("/")
async def inicio():
    return {
        "mensaje": "API Gateway del restaurante funcionando bien",
        "servicios": list(SERVICIOS),
    }

@app.api_route(
    "/api/{nombre_servicio}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
@app.api_route(
    "/api/{nombre_servicio}/{ruta:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy(
    nombre_servicio: str,
    request: Request,
    ruta: str = "",
):
    if nombre_servicio not in SERVICIOS:
        return JSONResponse(
            status_code=404,
            content={"detail": f"El servicio '{nombre_servicio}' no existe"},
        )
    url_base, prefijo = SERVICIOS[nombre_servicio]

    if ruta:
     url_destino = f"{url_base}{prefijo}/{ruta}"
    else:
     url_destino = f"{url_base}{prefijo}/"


    cabeceras = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in CABECERAS_IGNORADAS
    }

    id_correlacion = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
    cabeceras["X-Correlation-Id"] = id_correlacion

    try:
        async with httpx.AsyncClient(timeout=10.0) as cliente:
            respuesta = await cliente.request(
                method=request.method,
                url=url_destino,
                headers=cabeceras,
                params=list(request.query_params.multi_items()),
                content=await request.body(),
            )
    except httpx.RequestError:
        return JSONResponse(
            status_code=503,
            content={
                "detail": f"El servicio '{nombre_servicio}' no está disponible"
            },
            headers={"X-Correlation-Id": id_correlacion},
        )

    cabeceras_respuesta = {
        k: v
        for k, v in respuesta.headers.items()
        if k.lower() not in CABECERAS_IGNORADAS
    }
    cabeceras_respuesta["X-Correlation-Id"] = id_correlacion

    return Response(
        content=respuesta.content,
        status_code=respuesta.status_code,
        headers=cabeceras_respuesta,
    )
