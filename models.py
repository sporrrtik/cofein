from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    image_url = Column(String, nullable=False)
    price = Column(Integer, nullable=False)


class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(ForeignKey('users.email'), nullable=False)
    item_id = Column(ForeignKey('items.id'), nullable=False)

    owner = relationship('User')
    item = relationship('Item')


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(ForeignKey('users.email'), nullable=False)
    ordered_items = Column(String, nullable=False)
    total_price = Column(Integer, nullable=False)
    active = Column(Boolean, default=True)
