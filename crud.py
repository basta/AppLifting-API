from sqlalchemy.orm import Session
import models, schemas


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


def get_product_offers(db: Session, product_id: int):
    return db.query(models.Product).get(product_id).offers
