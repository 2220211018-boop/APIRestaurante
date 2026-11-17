from fastapi import FastAPI

from base_datos import engine, Base
import modelos.tablas

from rutas.rutas_inventario import enrutador as enrutador_inventario

# Crear las tablas de la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Servicio de Inventario")

app.include_router(enrutador_inventario)


@app.get("/")
def inicio():
    return {"mensaje": "Servicio de Inventario activo con base de datos PostgreSQL"}
