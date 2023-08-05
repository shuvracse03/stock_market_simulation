from celery import Celery
import time

from sqlalchemy.orm import Session
from fastapi import  HTTPException, Depends
from datetime import datetime
from . import models, schemas

from sqlalchemy import and_
import redis
import json
from pydantic.tools import parse_obj_as
from pydantic.json import pydantic_encoder

from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

    
# Dependency
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


BROKER="redis://redis:6379"

app = Celery("stock_market", backend="rpc://", broker=BROKER)

@app.task
def add():
    print('celery task started')
    for i in range(0,20):
        print('i:',i)
        time.sleep(1)
    return 3+4
    
 
    
    
@app.task    
def create_transaction_task(data):

    
    print('inside celery task')
    
    transaction = schemas.TransactionCreate(user_id = data['user_id'], ticker=data['ticker'], transaction_type=data['transaction_type'], transaction_volume=data['transaction_volume'])
    db = get_db()
    print(transaction)
    
    user = db.query(models.User).filter(models.User.user_id == transaction.user_id)
    
    if user.first() is None:
        raise HTTPException(status_code=404, detail="User not found")
    if transaction.transaction_type not in ['BUY','SELL']:
        raise HTTPException(status_code=400, detail="Invalid transaction type")
    result = db.query(models.StockData).filter(models.StockData.ticker == transaction.ticker).first()
    if result is None:
        raise HTTPException(status_code=404, detail="Stock not found")

    stock_details = db.query(models.StockData).filter(models.StockData.ticker == transaction.ticker).one()
    stock_price = stock_details.current_price
    transaction_price = stock_price * transaction.transaction_volume
    if transaction.transaction_type == "BUY":
        user_record = user.one()
        if user_record.balance < transaction_price:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        if stock_details.available_quantity< transaction.transaction_volume:
            raise HTTPException(status_code=400, detail="Insufficient stocks available")
        user_stock_qty = db.query(models.UserStockQuantity).filter(and_(models.UserStockQuantity.owner_id == user_record.id, models.UserStockQuantity.ticker == transaction.ticker))
        flag=True
        if user_stock_qty.first() is None:
           
            db_user_stock_quantity = models.UserStockQuantity(ticker=transaction.ticker, quantity = transaction.transaction_volume, owner_id = user_record.id)
            db.add(db_user_stock_quantity)
        else:
            record = user_stock_qty.one()
            record.ticker =transaction.ticker
            record.quantity =  record.quantity + transaction.transaction_volume
            record.owner_id = user_record.id
            flag=False
            
        user_record.balance -= transaction_price
        stock_details.volume += transaction.transaction_volume
        stock_details.available_quantity -= transaction.transaction_volume
        db_transaction = models.Transaction(ticker=transaction.ticker, transaction_type='BUY',\
         transaction_volume= transaction.transaction_volume, transaction_price = transaction_price, timestamp=datetime.now(), owner_id=user_record.id)
        db.add(db_transaction)
            
        db.commit()
        db.refresh(db_transaction)
        if flag:
           db.refresh(db_user_stock_quantity)
    else: #Sell
        user_record = user.one()
        db_user_stock_quantity = db.query(models.UserStockQuantity).filter(and_(models.UserStockQuantity.owner_id == user_record.id, models.UserStockQuantity.ticker == transaction.ticker))
        if db_user_stock_quantity.first() is None:
            raise HTTPException(status_code=400, detail="User has no stock")
        user_stock_record = db_user_stock_quantity.one()
        if user_stock_record.quantity < transaction.transaction_volume:
            raise HTTPException(status_code=400, detail="User has not sufficient stock")
       
        user_stock_record.quantity =  user_stock_record.quantity - transaction.transaction_volume
        user_record.balance += transaction_price
        stock_details.volume += transaction.transaction_volume
        stock_details.available_quantity += transaction.transaction_volume
        db_transaction = models.Transaction(ticker=transaction.ticker, transaction_type='SELL',\
         transaction_volume= transaction.transaction_volume, transaction_price = transaction_price, timestamp=datetime.now(), owner_id=user_record.id)
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        
    return ''
    
