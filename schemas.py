from pydantic import BaseModel
from typing import Union


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


Product.update_forward_refs()


class ProductUpdate(ProductBase):
    pass
