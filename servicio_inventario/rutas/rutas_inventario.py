import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from base_datos import obtener_db
from modelos.inventario import (
    ActualizarInventario,
    CrearInventario,
    MovimientoLote,
)
from modelos.tablas import InventarioTabla
from shared.middleware_seguridad import obtener_usuario_actual, requerir_rol

URL_PRODUCTOS = os.getenv(
    "URL_PRODUCTOS", "http://servicio_clientes_productos:8000"
)

enrutador = APIRouter(prefix="/inventario", tags=["Inventario"])


def a_dict(i: InventarioTabla) -> dict:
    return {
        "producto_id": i.producto_id,
        "stock": i.stock,
        "stock_minimo": i.stock_minimo,
        "bajo_minimo": i.stock <= i.stock_minimo,
        "agotado": i.stock <= 0,
        "actualizado_en": i.actualizado_en,
    }


def verificar_producto_existe(producto_id: int) -> None:
    """Comunicación entre microservicios: el producto debe existir en el menú."""
    try:
        with httpx.Client(timeout=5.0) as cliente:
            r = cliente.get(f"{URL_PRODUCTOS}/productos/{producto_id}")
    except httpx.RequestError:
        raise HTTPException(
            status_code=503, detail="El servicio de productos no está disponible"
        )
    if r.status_code == 404:
        raise HTTPException(
            status_code=400, detail=f"El producto {producto_id} no existe en el menú."
        )
    if r.status_code != 200:
        raise HTTPException(
            status_code=502, detail="Error consultando el servicio de productos"
        )


def agrupar(items) -> dict:
    """Suma cantidades por producto y ordena por id (evita bloqueos cruzados)."""
    totales = {}
    for it in items:
        totales[it.producto_id] = totales.get(it.producto_id, 0) + it.cantidad
    return dict(sorted(totales.items()))


# READ: productos con stock bajo (solo admin). Va antes de /{producto_id}.
@enrutador.get("/alertas")
def alertas_stock_bajo(
    db: Session = Depends(obtener_db),
    usuario: dict = Depends(requerir_rol(["ROLE_ADMIN"])),
):
    bajos = (
        db.query(InventarioTabla)
        .filter(InventarioTabla.stock <= InventarioTabla.stock_minimo)
        .order_by(InventarioTabla.stock)
        .all()
    )
    return [a_dict(i) for i in bajos]


# CREATE: registrar stock de un producto (solo admin)
@enrutador.post("/", status_code=status.HTTP_201_CREATED)
def registrar_inventario(
    datos: CrearInventario,
    db: Session = Depends(obtener_db),
    usuario: dict = Depends(requerir_rol(["ROLE_ADMIN"])),
):
    verificar_producto_existe(datos.producto_id)

    existente = (
        db.query(InventarioTabla)
        .filter(InventarioTabla.producto_id == datos.producto_id)
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=400, detail="Ese producto ya tiene inventario registrado."
        )

    nuevo = InventarioTabla(
        producto_id=datos.producto_id,
        stock=datos.stock,
        stock_minimo=datos.stock_minimo,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"mensaje": "Inventario registrado exitosamente", "inventario": a_dict(nuevo)}


# READ: listar todo el inventario (solo admin)
@enrutador.get("/")
def listar_inventario(
    db: Session = Depends(obtener_db),
    usuario: dict = Depends(requerir_rol(["ROLE_ADMIN"])),
):
    return [a_dict(i) for i in db.query(InventarioTabla).order_by(InventarioTabla.producto_id).all()]


# READ BY ID: consultar stock de un producto (usuario autenticado)
@enrutador.get("/{producto_id}")
def consultar_stock(
    producto_id: int,
    db: Session = Depends(obtener_db),
    usuario: dict = Depends(obtener_usuario_actual),
):
    registro = (
        db.query(InventarioTabla)
        .filter(InventarioTabla.producto_id == producto_id)
        .first()
    )
    if not registro:
        raise HTTPException(
            status_code=404, detail="Ese producto no tiene inventario registrado."
        )
    return a_dict(registro)


# UPDATE: fijar stock y mínimo (solo admin)
@enrutador.put("/{producto_id}")
def actualizar_inventario(
    producto_id: int,
    datos: ActualizarInventario,
    db: Session = Depends(obtener_db),
    usuario: dict = Depends(requerir_rol(["ROLE_ADMIN"])),
):
    registro = (
        db.query(InventarioTabla)
        .filter(InventarioTabla.producto_id == producto_id)
        .first()
    )
    if not registro:
        raise HTTPException(
            status_code=404, detail="Ese producto no tiene inventario registrado."
        )
    registro.stock = datos.stock
    registro.stock_minimo = datos.stock_minimo
    db.commit()
    db.refresh(registro)
    return {"mensaje": "Inventario actualizado", "inventario": a_dict(registro)}


# DELETE: dejar de controlar el inventario de un producto (solo admin)
@enrutador.delete("/{producto_id}")
def eliminar_inventario(
    producto_id: int,
    db: Session = Depends(obtener_db),
    usuario: dict = Depends(requerir_rol(["ROLE_ADMIN"])),
):
    registro = (
        db.query(InventarioTabla)
        .filter(InventarioTabla.producto_id == producto_id)
        .first()
    )
    if not registro:
        raise HTTPException(
            status_code=404, detail="Ese producto no tiene inventario registrado."
        )
    db.delete(registro)
    db.commit()
    return {"mensaje": "Inventario eliminado exitosamente"}


# DESCONTAR: lo llama el servicio de pedidos al crear un pedido.
# Es atómico: o se descuentan todos los ítems o no se descuenta ninguno.
# Los productos sin registro de inventario no se controlan (se permiten).
@enrutador.post("/descontar")
def descontar_stock(
    datos: MovimientoLote,
    db: Session = Depends(obtener_db),
    usuario: dict = Depends(obtener_usuario_actual),
):
    totales = agrupar(datos.items)
    registros = {}
    for producto_id, cantidad in totales.items():
        reg = (
            db.query(InventarioTabla)
            .filter(InventarioTabla.producto_id == producto_id)
            .with_for_update()
            .first()
        )
        if reg is None:
            continue
        if reg.stock < cantidad:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Stock insuficiente para el producto {producto_id}: "
                    f"disponible {reg.stock}, solicitado {cantidad}."
                ),
            )
        registros[producto_id] = reg

    for producto_id, reg in registros.items():
        reg.stock -= totales[producto_id]
    db.commit()
    return {"mensaje": "Stock descontado", "productos": list(registros)}


# REPONER: lo llama pedidos al cancelar un pedido (solo admin).
@enrutador.post("/reponer")
def reponer_stock(
    datos: MovimientoLote,
    db: Session = Depends(obtener_db),
    usuario: dict = Depends(requerir_rol(["ROLE_ADMIN"])),
):
    totales = agrupar(datos.items)
    repuestos = []
    for producto_id, cantidad in totales.items():
        reg = (
            db.query(InventarioTabla)
            .filter(InventarioTabla.producto_id == producto_id)
            .with_for_update()
            .first()
        )
        if reg is None:
            continue
        reg.stock += cantidad
        repuestos.append(producto_id)
    db.commit()
    return {"mensaje": "Stock repuesto", "productos": repuestos}
