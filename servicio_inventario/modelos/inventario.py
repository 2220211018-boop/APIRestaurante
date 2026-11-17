from typing import List

from pydantic import BaseModel, Field


class CrearInventario(BaseModel):
    producto_id: int = Field(..., examples=[1])
    stock: int = Field(..., ge=0, examples=[50])
    stock_minimo: int = Field(default=5, ge=0, examples=[5])


class ActualizarInventario(BaseModel):
    stock: int = Field(..., ge=0, examples=[40])
    stock_minimo: int = Field(default=5, ge=0, examples=[5])


class ItemMovimiento(BaseModel):
    producto_id: int = Field(..., examples=[1])
    cantidad: int = Field(..., gt=0, examples=[2])


class MovimientoLote(BaseModel):
    items: List[ItemMovimiento]
