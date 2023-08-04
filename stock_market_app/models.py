from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship

from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, index=True)
    username = Column(String)
    balance = Column(Float, default=0)
    transactions = relationship("Transaction", back_populates="user")
    user_stock_quantities = relationship("UserStockQuantity", back_populates="user")
    
class UserStockQuantity(Base):
    __tablename__ = "user_stock_quantity"

    id = Column(Integer, primary_key=True)
    ticker = Column(String)
    quantity= Column(Float, default=0)
    owner_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", back_populates="user_stock_quantities") 
    
class StockData(Base):
    __tablename__ = "stock_data"

    id = Column(Integer, primary_key=True)
    ticker = Column(String)
    open_price = Column(Float, default=0)
    close_price = Column(Float, default=0)
    high = Column(Float, default=0)
    low = Column(Float, default=0)
    volume = Column(Float, default=0)
    available_quantity = Column(Float, default=0)
    current_price = Column(Float, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transaction"

    transaction_id = Column(Integer, primary_key=True)
    ticker = Column(String)
    transaction_type = Column(String)
    transaction_volume= Column(Float, default=0)
    transaction_price = Column(Float, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    owner_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", back_populates="transactions")
