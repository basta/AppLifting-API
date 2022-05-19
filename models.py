from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship

import database
from database import BaseDbModel


class Product(BaseDbModel):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    desc = Column(String)
    offers = relationship("Offer")

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


class Offer(BaseDbModel):
    __tablename__ = "offers"
    id = Column(Integer, primary_key=True, index=True)
    price = Column(Float)
    items_in_stock = Column(Integer)
    product_id = Column(Integer, ForeignKey("products.id"))


# Product.update_forward_refs()
