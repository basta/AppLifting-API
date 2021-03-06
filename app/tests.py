import datetime
import time

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.schemas as schemas
import app.crud as crud
from app.database import BaseDbModel
from app.main import get_db, app
from app.offers_ms import OffersAPI

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

BaseDbModel.metadata.create_all(bind=engine)

client = TestClient(app)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

BASE_URL = "https://applifting-python-excercise-ms.herokuapp.com/api/v1"
offersAPI = OffersAPI(BASE_URL)

# Get token for testing
offersAPI.refresh_token()


def test_create_product():
    response = client.post(
        "/products", json={"name": "sekačka", "desc": "Nejlepší sekačka na světě"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "sekačka"
    assert "id" in data
    product_id = data["id"]

    # Try reading the product from database
    response = client.get(f"/products/{product_id}")
    assert (
        response.status_code == 200
    ), f"Product id:{product_id} not found in database after creation"
    data = response.json()
    assert data["name"] == "sekačka"
    assert data["id"] == product_id


def test_delete_product():
    """Successful case and a failing case"""
    # create the product
    response = client.post(
        "/products", json={"name": "sekačka", "desc": "Nejlepší sekačka na světě"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "sekačka"
    assert "id" in data
    product_id = data["id"]

    # Delete product
    response = client.delete(f"/products/{product_id}")
    assert response.status_code == 200, response.text
    assert response.json()

    response = client.get(f"/products/{product_id}")
    assert response.status_code == 404


def test_update_product():
    """Successful case and a failing case"""
    response = client.post(
        "/products", json={"name": "sekačka", "desc": "Nejlepší sekačka na světě"}
    )
    assert response.status_code == 200
    product_id = response.json()["id"]

    response = client.put(
        f"/products/{product_id}", json={"name": "akčakes", "desc": "Už není nejlepší"}
    )
    assert response.status_code == 200, response.text

    # Read after the update
    response = client.get(f"/products/{product_id}")
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["name"] == "akčakes", "Failed updating name"
    assert data["desc"] == "Už není nejlepší", "Failed updating desc"


def test_update_offers_for_product():
    db = TestingSessionLocal()
    db_product = crud.create_product(
        db, schemas.ProductCreate(name="Sekačka", desc="nejlepší")
    )
    mock_offers_data = [
        {"id": 1, "price": 1000, "items_in_stock": 2},
        {"id": 2, "price": 230, "items_in_stock": 1},
        {"id": 4, "price": 10020, "items_in_stock": 0},
    ]
    db_product.update_offers(db, mock_offers_data)

    db_product_offers = db_product.offers
    for i in range(3):
        assert db_product_offers[i].price == mock_offers_data[i]["price"]
        assert (
            db_product_offers[i].items_in_stock == mock_offers_data[i]["items_in_stock"]
        )


# Integration tests for the Offers microservice


def test_register_product():
    db_product = crud.create_product(
        TestingSessionLocal(), schemas.ProductCreate(name="Sekačka", desc="nejlepší")
    )
    response = offersAPI.register_product(db_product)
    assert int(response["id"]) == db_product.id


def test_offers_for_product():
    db_product = crud.create_product(
        TestingSessionLocal(), schemas.ProductCreate(name="Sekačka", desc="nejlepší")
    )
    offersAPI.register_product(db_product)
    data = offersAPI.get_offers_for_product(db_product)
    assert isinstance(data, list)


def test_update_product_offers():
    """
    There is nothing we know about the offers we can expect,
    so we only check whether updates executes without error
    """
    db = TestingSessionLocal()
    db_product = crud.create_product(
        db, schemas.ProductCreate(name="Sekačka", desc="nejlepší")
    )

    # Update after registering
    offersAPI.register_product(db_product)
    db_product.update_offers(db, offersAPI.get_offers_for_product(db_product))


def test_creating_product_snapshot():
    db = TestingSessionLocal()
    db_product = crud.create_product(
        db, schemas.ProductCreate(name="Sekačka", desc="nejlepší")
    )
    offersAPI.register_product(db_product)
    offers = offersAPI.get_offers_for_product(db_product)
    db_product.add_snapshot_average_price(db, offers)
    db.refresh(db_product)
    snapshot = db_product.price_snapshots[0]
    assert isinstance(snapshot.price, float)


def test_price_interpolation():
    db = TestingSessionLocal()
    db_product = crud.create_product(
        db, schemas.ProductCreate(name="Sekačka", desc="nejlepší")
    )
    db_product.add_snapshot(db, 100, datetime.datetime.now())
    db_product.add_snapshot(
        db, 200, datetime.datetime.now() + datetime.timedelta(seconds=60)
    )
    db.refresh(db_product)
    assert (
        db_product.interpolate_price_at_time(
            db, datetime.datetime.now() - datetime.timedelta(minutes=1)
        ).price
        == 100
    )

    assert (
        db_product.interpolate_price_at_time(
            db, datetime.datetime.now() + datetime.timedelta(minutes=1)
        ).price
        == 200
    )


def test_price_change():
    db = TestingSessionLocal()
    db_product = crud.create_product(
        db, schemas.ProductCreate(name="Sekačka", desc="nejlepší")
    )
    db_product.add_snapshot(db, 100, datetime.datetime.now())
    db_product.add_snapshot(db, 231, datetime.datetime.now())
    db_product.add_snapshot(db, 242, datetime.datetime.now())
    db_product.add_snapshot(
        db, 200, datetime.datetime.now() + datetime.timedelta(minutes=1)
    )
    db_product.add_snapshot(
        db, 200, datetime.datetime.now() + datetime.timedelta(minutes=2)
    )
    change = crud.get_product_price_change(
        db,
        db_product.id,
        from_time=datetime.datetime.now() - datetime.timedelta(minutes=1),
        to_time=datetime.datetime.now() + datetime.timedelta(minutes=1),
    )

    assert change == 2.0
