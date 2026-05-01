from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from app.models.character import Currency


class ItemCreate(BaseModel):
    name: str
    quantity: int = 1
    weight: float = 0.0
    description: str = ""
    item_type: str = "misc"
    equipped: bool = False
    attuned: bool = False
    properties: dict = Field(default_factory=dict)


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[int] = None
    weight: Optional[float] = None
    description: Optional[str] = None
    item_type: Optional[str] = None
    equipped: Optional[bool] = None
    attuned: Optional[bool] = None
    properties: Optional[dict] = None


class CurrencyUpdate(BaseModel):
    cp: Optional[int] = None
    sp: Optional[int] = None
    ep: Optional[int] = None
    gp: Optional[int] = None
    pp: Optional[int] = None
