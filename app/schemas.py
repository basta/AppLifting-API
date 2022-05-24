import datetime

from pydantic import BaseModel
from typing import Union

from app import models


class ProductBase(BaseModel):
    name: str
    desc: str


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int
    offers: "list[Offer]"

    class Config:
        orm_mode = True


class Offer(BaseModel):
    id: int
    price: float
    product: Product

    class Config:
        orm_mode = True


class ProductUpdate(ProductBase):
    pass


class OfferList(BaseModel):
    offers: list[Offer]

    class Config:
        orm_mode = True


class PriceSnapshot(BaseModel):
    price: float
    time: datetime.datetime


class PriceHistory(BaseModel):
    history: list[PriceSnapshot]

    class Config:
        orm_mode = True


Product.update_forward_refs()
