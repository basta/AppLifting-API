import datetime
import math
from typing import Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship

import app.database as database
from app.database import BaseDbModel


class Product(BaseDbModel):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    desc = Column(String)
    offers = relationship("Offer")
    price_snapshots = relationship("PriceSnapshot")

    def update_offers(self, db: database.SessionLocal, new_offers: list[dict]):
        """

        :param db: DbSession
        :param new_offers: List of dict representing offers
        """
        # Delete existing offers
        for old_offer in self.offers:
            db.delete(old_offer)

        self.offers = []
        # Create new offers
        for new_offer_data in new_offers:
            new_offer = Offer(
                price=new_offer_data["price"],
                product_id=new_offer_data["id"],
                items_in_stock=new_offer_data["items_in_stock"],
            )
            db.add(new_offer)

            self.offers.append(new_offer)

        db.commit()

    def add_snapshot(self, db, price, time=None):
        """Add a snapshot of a price at time now"""
        time = time or datetime.datetime.now()
        snapshot = PriceSnapshot(price=price, time=time, product_id=self.id)
        db.add(snapshot)
        db.commit()

    def add_snapshot_average_price(self, db, offers: list[dict]):
        """Save a snapshot of average price of this product into database"""
        avg_price = sum(offer["price"] for offer in offers) / len(offers)
        self.add_snapshot(db, avg_price)

    def interpolate_price_at_time(
        self, db, time: datetime.datetime
    ) -> Optional["PriceSnapshot"]:
        """Interpolate the price of product at time using nearest interpolation"""
        time = time or datetime.datetime.now()
        snaps = self.price_snapshots
        if not snaps:
            return None
        nearest_snap = snaps[0]
        for snap in snaps[1:]:
            # If snap is closer to time
            if abs((snap.time - time).total_seconds()) < abs(
                (nearest_snap.time - time).total_seconds()
            ):
                nearest_snap = snap

        return nearest_snap


class Offer(BaseDbModel):
    __tablename__ = "offers"
    id = Column(Integer, primary_key=True, index=True)
    price = Column(Float)
    items_in_stock = Column(Integer)
    product_id = Column(Integer, ForeignKey("products.id"))


class PriceSnapshot(BaseDbModel):
    """Model holding a price of a model at a given time"""

    __tablename__ = "PriceSnapshots"
    id = Column(Integer, primary_key=True, index=True)
    price = Column(Float)
    product_id = Column(Integer, ForeignKey("products.id"))
    time = Column(DateTime)
