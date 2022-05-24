import os

from fastapi import Depends, FastAPI, HTTPException, BackgroundTasks

from sqlalchemy.orm import Session
import asyncio

import app.crud as crud
import app.models as models
import app.schemas as schemas
from app.database import SessionLocal, engine
from app.offers_ms import OffersAPI

import datetime

models.BaseDbModel.metadata.create_all(bind=engine)

app = FastAPI()

# dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


offersAPI = OffersAPI(base_url=os.environ["BASE_URL_OFFERS"])
offersAPI.refresh_token()


async def offers_updater():
    """
    Async worker running every 60s that updates product's offers and saves its average price snapshot
    """
    db: Session = SessionLocal()
    while True:
        products: list[models.Product] = db.query(models.Product).all()
        for product in products:
            offers = offersAPI.get_offers_for_product(product)

            product.update_offers(db, offers)

        await asyncio.sleep(60)


@app.on_event("startup")
async def start_offers_updater():
    asyncio.create_task(offers_updater())


@app.get("/health")
def root():
    return {"health": "OK"}


@app.post("/products", response_model=schemas.Product)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
):
    return crud.create_product(db, product)


@app.get("/products/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    if db_product := crud.get_product(db, product_id):
        return db_product
    else:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")


@app.delete("/products/{product_id}", response_model=bool)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    if db_product := crud.delete_product(db, product_id):
        return db_product
    else:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")


@app.put("/products/{product_id}", response_model=schemas.Product)
def update_product(
    product_id: int, new_product: schemas.ProductUpdate, db: Session = Depends(get_db)
):
    if db_product := crud.update_product(db, product_id, new_product):
        return db_product
    else:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")


@app.get("/products/{product_id}/offers", response_model=schemas.OfferList)
def get_offers(product_id: int, db: Session = Depends(get_db)):
    if offers := crud.get_product_offers(db, product_id):
        return {"offers": offers}
    else:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")


@app.get("/products/{product_id}/history", response_model=schemas.PriceHistory)
def get_price_history(product_id: int, db: Session = Depends(get_db)):
    if history := crud.get_product_history(db, product_id) is not None:
        return {"history": history}
    else:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")


@app.get("/products/{product_id}/price-change", response_model=float)
def get_price_change(
    product_id: int,
    from_time: datetime.datetime,
    to_time: datetime.datetime,
    db: Session = Depends(get_db),
):
    crud.get_product_price_change(db, product_id, from_time, to_time)
