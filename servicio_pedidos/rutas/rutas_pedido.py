import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from base_datos import obtener_db
from modelos.pedido import ActualizarEstado, CrearPedido
from modelos.tablas import ItemPedidoTabla, PedidoTabla
from shared.middleware_seguridad import obtener_usuario_actual, requerir_rol

URL_PRODUCTOS = os.getenv(
    "URL_PRODUCTOS", "http://servicio_clientes_productos:8000"
)

URL_INVENTARIO = os.getenv(
    "URL_INVENTARIO", "http://servicio_inventario:8000"
)

ESTADOS_VALIDOS = ["PENDIENTE", "EN_PREPARACION", "EN_CAMINO", "ENTREGADO", "CANCELADO"]

enrutador = APIRouter(prefix="/pedidos", tags=["Pedidos"])


def a_dict(pedido: PedidoTabla) -> dict:
    return {
        "id": pedido.id,
        "usuario_id": pedido.usuario_id,
        "direccion_entrega": pedido.direccion_entrega,
        "estado": pedido.estado,
        "total": pedido.total,
        "creado_en": pedido.creado_en,
        "items": [
            {
                "producto_id": i.producto_id,
                "nombre_producto": i.nombre_producto,
                "cantidad": i.cantidad,
                "precio_unitario": i.precio_unitario,
                "subtotal": i.cantidad * i.precio_unitario,
            }
            for i in pedido.items
        ],
    }


def consultar_producto(producto_id: int) -> dict:
    """Comunicación entre microservicios: consulta el precio real al servicio de productos."""
    try:
        with httpx.Client(timeout=5.0) as cliente:
            r = cliente.get(f"{URL_PRODUCTOS}/productos/{producto_id}")
    except httpx.RequestError:
        raise HTTPException(
            status_code=503, detail="El servicio de productos no está disponible"
        )
    if r.status_code == 404:
        raise HTTPException(
            status_code=400, detail=f"El producto {producto_id} no existe"
        )
    if r.status_code != 200:
        raise HTTPException(
            status_code=502, detail="Error consultando el servicio de productos"
        )
    return r.json()


def mover_inventario(accion: str, items: list, authorization: str) -> None:
    """Llama al servicio de inventario ('descontar' o 'reponer') reenviando el JWT del usuario."""
    try:
        with httpx.Client(timeout=5.0) as cliente:
            r = cliente.post(
                f"{URL_INVENTARIO}/inventario/{accion}",
                json={"items": items},
                headers={"Authorization": authorization or ""},
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503, detail="El servicio de inventario no está disponible"
        )
    if r.status_code == 409:
        raise HTTPException(status_code=409, detail=r.json().get("detail"))
    if r.status_code != 200:
        raise HTTPException(
            status_code=502, detail="Error consultando el servicio de inventario"
        )


def obtener_pedido_autorizado(pedido_id: int, db: Session, usuario: dict) -> PedidoTabla:
    pedido = db.query(PedidoTabla).filter(PedidoTabla.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    # Un usuario normal solo puede ver sus propios pedidos
    if usuario["rol"] != "ROLE_ADMIN" and pedido.usuario_id != usuario["usuario"]:
        raise HTTPException(status_code=403, detail="No puedes ver este pedido.")
    return pedido


# CREATE: crear pedido (cualquier usuario autenticado)
@enrutador.post("/", status_code=status.HTTP_201_CREATED)
def crear_pedido(
    datos: CrearPedido,
    request: Request,
    db: Session = Depends(obtener_db),
    usuario: dict = Depends(obtener_usuario_actual),
):
    if not datos.items:
        raise HTTPException(status_code=400, detail="El pedido no tiene productos.")

    pedido = PedidoTabla(
        usuario_id=usuario["usuario"],
        direccion_entrega=datos.direccion_entrega,
        estado="PENDIENTE",
    )

    total = 0.0
    for item in datos.items:
        producto = consultar_producto(item.producto_id)
        if not producto.get("disponible", True):
            raise HTTPException(
                status_code=400,
                detail=f"El producto '{producto['nombre']}' no está disponible.",
            )
        total += producto["precio"] * item.cantidad
        pedido.items.append(
            ItemPedidoTabla(
                producto_id=item.producto_id,
                nombre_producto=producto["nombre"],
                cantidad=item.cantidad,
                precio_unitario=producto["precio"],
            )
        )

    # Descuenta el stock (409 si no alcanza). Si falla, no se crea el pedido.
    mover_inventario(
        "descontar",
        [{"producto_id": i.producto_id, "cantidad": i.cantidad} for i in datos.items],
        request.headers.get("authorization"),
    )

    pedido.total = total
    db.add(pedido)
    db.commit()
    db.refresh(pedido)

    return {"mensaje": "Pedido creado exitosamente", "pedido": a_dict(pedido)}


# READ: listar pedidos (admin ve todos, usuario ve los suyos)
@enrutador.get("/")
def listar_pedidos(
    db: Session = Depends(obtener_db),
    usuario: dict = Depends(obtener_usuario_actual),
):
    consulta = db.query(PedidoTabla)
    if usuario["rol"] != "ROLE_ADMIN":
        consulta = consulta.filter(PedidoTabla.usuario_id == usuario["usuario"])
    return [a_dict(p) for p in consulta.order_by(PedidoTabla.id.desc()).all()]


# READ BY ID
@enrutador.get("/{pedido_id}")
def obtener_pedido(
    pedido_id: int,
    db: Session = Depends(obtener_db),
    usuario: dict = Depends(obtener_usuario_actual),
):
    return a_dict(obtener_pedido_autorizado(pedido_id, db, usuario))


# UPDATE: cambiar estado (solo admin)
@enrutador.put("/{pedido_id}")
def actualizar_estado(
    pedido_id: int,
    datos: ActualizarEstado,
    request: Request,
    db: Session = Depends(obtener_db),
    usuario: dict = Depends(requerir_rol(["ROLE_ADMIN"])),
):
    estado = datos.estado.upper()
    if estado not in ESTADOS_VALIDOS:
        raise HTTPException(
            status_code=400, detail=f"Estado inválido. Use uno de: {ESTADOS_VALIDOS}"
        )
    pedido = db.query(PedidoTabla).filter(PedidoTabla.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")

    # Al cancelar un pedido se devuelve el stock al inventario
    if estado == "CANCELADO" and pedido.estado != "CANCELADO":
        mover_inventario(
            "reponer",
            [{"producto_id": i.producto_id, "cantidad": i.cantidad} for i in pedido.items],
            request.headers.get("authorization"),
        )

    pedido.estado = estado
    db.commit()
    db.refresh(pedido)
    return {"mensaje": "Estado actualizado", "pedido": a_dict(pedido)}


# DELETE: eliminar pedido (solo admin)
@enrutador.delete("/{pedido_id}")
def eliminar_pedido(
    pedido_id: int,
    db: Session = Depends(obtener_db),
    usuario: dict = Depends(requerir_rol(["ROLE_ADMIN"])),
):
    pedido = db.query(PedidoTabla).filter(PedidoTabla.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    db.delete(pedido)
    db.commit()
    return {"mensaje": "Pedido eliminado exitosamente"}
