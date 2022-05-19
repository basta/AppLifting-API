import os

from fastapi import Depends, FastAPI, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import asyncio

import crud, models, schemas
from database import SessionLocal, engine
from offers_ms import OffersAPI

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
    db: Session = SessionLocal()
    while True:
        products: list[models.Product] = db.query(models.Product).all()
        for product in products:
            product.update_offers(db, offersAPI.get_offers_for_product(product))

        await asyncio.sleep(60)


@app.on_event("startup")
async def start_offers_updater():
    asyncio.create_task(offers_updater())


@app.get("/")
def root(background_tasks: BackgroundTasks):
    return {"message": "Hello World"}


@app.post("/products", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
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


@app.put("/products/{product_id}")
def update_product(
    product_id: int, new_product: schemas.ProductUpdate, db: Session = Depends(get_db)
):
    if db_product := crud.update_product(db, product_id, new_product):
        return db_product
    else:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")


@app.get("/products/{product_id}/offers")
def get_offers(product_id: int, db: Session = Depends(get_db)):
    return crud.get_product_offers(db, product_id)
