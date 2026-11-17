from fastapi import APIRouter, Depends
from modelos.pago import CrearPago
from shared.middleware_seguridad import obtener_usuario_actual

enrutador = APIRouter(
    prefix="/pagos", tags=["Pagos"], dependencies=[Depends(obtener_usuario_actual)]
)
base_datos_pagos = []

@enrutador.post("/")
async def procesar_pago(pago: CrearPago):
    datos = pago.dict()
    datos["id"] = str(len(base_datos_pagos) + 1)
    base_datos_pagos.append(datos)
    return {"id": datos["id"], "mensaje": "Pago registrado con éxito", "datos": datos}

@enrutador.get("/")
async def obtener_pagos():
    return base_datos_pagos