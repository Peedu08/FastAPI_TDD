from datetime import datetime

from typing import List
from uuid import UUID

from requests import Session
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import pymongo
from store.db.mongo import db_client
from store.models.product import ProductModel
from store.schemas.product import ProductIn, ProductOut, ProductUpdate, ProductUpdateOut
from store.core.exceptions import NotFoundException


class ProductUsecase:
    def __init__(self, db: Session = SessionLocal()):
        self.db = db

    async def create(self, body: ProductIn) -> ProductOut:
        product = Product(**body.dict())
        try:
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
        except Exception as e:
            self.db.rollback()
            raise InsertionError()
        return ProductOut.from_orm(product)

    async def get(self, id: UUID4) -> ProductOut:
        product = self.db.query(Product).filter(Product.id == id).first()
        if not product:
            raise NotFoundException()
        return ProductOut.from_orm(product)

    async def query(self) -> List[ProductOut]:
        products = self.db.query(Product).all()
        return [ProductOut.from_orm(product) for product in products]

    async def update(self, id: UUID4, body: ProductUpdate) -> ProductUpdateOut:
        product = self.db.query(Product).filter(Product.id == id).first()
        if not product:
            raise NotFoundException()
        for key, value in body.dict(exclude_unset=True).items():
            setattr(product, key, value)
        product.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(product)
        return ProductUpdateOut.from_orm(product)

    async def delete(self, id: UUID4) -> None:
        product = self.db.query(Product).filter(Product.id == id).first()
        if not product:
            raise NotFoundException()
        self.db.delete(product)
        self.db.commit()

    async def filter_by_price(self, min_price: float, max_price: float) -> List[ProductOut]:
        products = self.db.query(Product).filter(Product.price > min_price, Product.price < max_price).all()
        return [ProductOut.from_orm(product) for product in products]


product_usecase = ProductUsecase()
