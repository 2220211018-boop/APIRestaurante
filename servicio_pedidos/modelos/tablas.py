from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from base_datos import Base


class PedidoTabla(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(String(50), nullable=False, index=True)
    direccion_entrega = Column(String(255), nullable=False)
    estado = Column(String(30), nullable=False, default="PENDIENTE")
    total = Column(Float, nullable=False, default=0)
    creado_en = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    items = relationship(
        "ItemPedidoTabla", back_populates="pedido", cascade="all, delete-orphan"
    )


class ItemPedidoTabla(Base):
    __tablename__ = "pedido_items"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    producto_id = Column(Integer, nullable=False)
    nombre_producto = Column(String(100), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)

    pedido = relationship("PedidoTabla", back_populates="items")
