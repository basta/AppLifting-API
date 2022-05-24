import datetime
from typing import Optional

from sqlalchemy.orm import Session
import app.models as models
import app.schemas as schemas


def get_product(db: Session, product_id: int):
    return db.query(models.Product).get(product_id)


def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(name=product.name, desc=product.desc)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(db: Session, product_id: int, new_product: schemas.ProductUpdate):
    if db_product := db.query(models.Product).get(product_id):
        # Could be automated to replace all attributes using a loop
        db_product.desc = new_product.desc
        db_product.name = new_product.name
        db.commit()
        return db_product
    else:
        return None


def delete_product(db: Session, product_id: int) -> bool:
    if db_product := db.query(models.Product).get(product_id):
        db.delete(db_product)
        db.commit()
        return True
    else:
        return False


def get_product_offers(db: Session, product_id: int) -> Optional[models.Offer]:
    db_product = db.query(models.Product).get(product_id)
    if db_product is None:
        return None

    return db_product.offers


def get_product_history(db: Session, product_id: int) -> Optional[models.PriceSnapshot]:
    db_product = db.query(models.Product).get(product_id)
    if db_product is None:
        return None

    return db_product.price_snapshots


def get_product_price_change(
    db: Session,
    product_id: int,
    from_time: datetime.datetime,
    to_time: datetime.datetime,
) -> Optional[float]:
    """
    Return relative price change between from `from_time` to `to_time`
    e.g. 100 -> 200: price change is 2
         100 -> 50: price change is 0.5
    """
    db_product: models.Product = db.query(models.Product).get(product_id)
    if db_product is None:
        return None

    start_price = db_product.interpolate_price_at_time(db, from_time).price
    end_price = db_product.interpolate_price_at_time(db, to_time).price
    return end_price / start_price
