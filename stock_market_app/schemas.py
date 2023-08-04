from pydantic import BaseModel
         

from datetime import date, datetime, time, timedelta

class UserStockQuantityBase(BaseModel):
    ticker: str
    quantity: float
    timestamp: datetime


class UserStockQuantityCreate(UserStockQuantityBase):
    user_id: str
    
class StockDataBase(BaseModel):
    ticker: str
    open_price: str 
    close_price: float
    high: float
    low: float
    volume: float
    available_quantity: float
    current_price: float
    timestamp: datetime


class StockDataCreate(StockDataBase):
    pass


class StockData(StockDataBase):
    id: int
    class Config:
        orm_mode = True
        
        
class TransactionBase(BaseModel):
    
    ticker: str
    transaction_type: str 
    transaction_volume: float
    #transaction_price: float
    #timestamp: datetime


class TransactionCreate(TransactionBase):
    user_id: str


class Transaction(TransactionBase):
    transaction_id: int
    owner_id: int
    transaction_price: float
    timestamp: datetime
    class Config:
        orm_mode = True
        

class UserBase(BaseModel):
    user_id: str
    username: str
    balance: float
    

class UserCreate(UserBase):
    pass
    
class User(UserBase):
    transactions: list[Transaction] = []

    class Config:
        orm_mode = True
        

