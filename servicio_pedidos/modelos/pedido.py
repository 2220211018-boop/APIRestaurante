from typing import List

from pydantic import BaseModel, Field


class ItemPedido(BaseModel):
    producto_id: int = Field(..., examples=[1])
    cantidad: int = Field(..., gt=0, examples=[2])


class CrearPedido(BaseModel):
    direccion_entrega: str = Field(..., examples=["Calle 10 # 5-20, Ibagué"])
    items: List[ItemPedido]


class ActualizarEstado(BaseModel):
    estado: str = Field(..., examples=["EN_PREPARACION"])
