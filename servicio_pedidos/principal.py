from fastapi import FastAPI

from base_datos import engine, Base
import modelos.tablas

from rutas.rutas_pedido import enrutador as enrutador_pedidos

# Crear las tablas de la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Servicio de Pedidos")

app.include_router(enrutador_pedidos)


@app.get("/")
def inicio():
    return {"mensaje": "Servicio de Pedidos activo con base de datos PostgreSQL"}
