from fastapi import APIRouter, Depends
from modelos.domicilio import CrearDomicilio
from shared.middleware_seguridad import obtener_usuario_actual

enrutador = APIRouter(
    prefix="/domicilios", tags=["Domicilios"], dependencies=[Depends(obtener_usuario_actual)]
)
base_datos_domicilios = []

@enrutador.post("/")
async def asignar_domicilio(domicilio: CrearDomicilio):
    datos = domicilio.dict()
    datos["id"] = str(len(base_datos_domicilios) + 1)
    base_datos_domicilios.append(datos)
    return {"id": datos["id"], "mensaje": "Domicilio asignado exitosamente", "datos": datos}

@enrutador.get("/")
async def obtener_domicilios():
    return base_datos_domicilios