from fastapi import FastAPI
from fastapi.testclient import TestClient
from .main import *
import json
from datetime import datetime, timedelta
from .database import SessionLocal, engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import pytest

db =SessionLocal()
client = TestClient(app)

#test buy transaction
def test_transaction_buy():
    user = db.query(models.User).filter(models.User.username == 'shuvra3').first()
    if user is not None:
       db.query(models.UserStockQuantity).filter(models.UserStockQuantity.user == user).delete()
       db.query(models.Transaction).filter(models.Transaction.user == user).delete()
       db.query(models.User).filter(models.User.username == 'shuvra3').delete()
       db.commit()
       

    api='/users/'
    data = {"username":"shuvra3","user_id":"shuvra3","balance":"50000"}
    
    response = client.post(
        api,
        json=data
    )

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    stock_data = db.query(models.StockData).filter(models.StockData.ticker == 'GOOGLE')
    
    if stock_data is not None:

      stock_data.delete()
      db.commit()
  
    data1 = {"ticker":"GOOGLE","open_price":"88","close_price":"91","high":"101","low":"81","volume":"0","current_price":"200","available_quantity":"2000", "timestamp":current_time}
    #create stock
    api='/stocks/'
    response = client.post(
        api,
        json=data1
    )
    time.sleep(0.5)
    stock = db.query(models.StockData).filter(models.StockData.ticker == 'GOOGLE').first()
   
    
    api='/transactions/'
    data = {"user_id":"shuvra3","ticker":"GOOGLE","transaction_type":"BUY","transaction_volume":"2"}
    response = client.post(
        api,
        json=data
    )
    
    time.sleep(2)
    user = db.query(models.User).filter(models.User.username == 'shuvra3').first()
    transaction = db.query(models.Transaction).filter().first()
    
    db.commit()
    stock = db.query(models.StockData).filter(models.StockData.ticker == 'GOOGLE').first()
    user_stock = db.query(models.UserStockQuantity).filter(models.UserStockQuantity.user == user).first()
    
    assert (user.balance == 49600) and ( stock.available_quantity ==1998) and (transaction.transaction_volume ==2) and (user_stock.quantity==2)
    
    
def test_transaction_sell():
    user = db.query(models.User).filter(models.User.username == 'shuvra3').first()
    if user is not None:
       db.query(models.UserStockQuantity).filter(models.UserStockQuantity.user == user).delete()
       db.query(models.Transaction).filter(models.Transaction.user == user).delete()
       db.query(models.User).filter(models.User.username == 'shuvra3').delete()
       db.commit()
       

    api='/users/'
    data = {"username":"shuvra3","user_id":"shuvra3","balance":"50000"}
    
    response = client.post(
        api,
        json=data
    )

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    stock_data = db.query(models.StockData).filter(models.StockData.ticker == 'GOOGLE')
    
    if stock_data is not None:

      stock_data.delete()
      db.commit()
  
    data1 = {"ticker":"GOOGLE","open_price":"88","close_price":"91","high":"101","low":"81","volume":"0","current_price":"200","available_quantity":"2000", "timestamp":current_time}
    #create stock
    api='/stocks/'
    response = client.post(
        api,
        json=data1
    )
    time.sleep(0.5)
    stock = db.query(models.StockData).filter(models.StockData.ticker == 'GOOGLE').first()
   
    
    api='/transactions/'
    data = {"user_id":"shuvra3","ticker":"GOOGLE","transaction_type":"BUY","transaction_volume":"2"}
    response = client.post(
        api,
        json=data
    )
    
    time.sleep(3.0)
    api='/transactions/'
    data = {"user_id":"shuvra3","ticker":"GOOGLE","transaction_type":"SELL","transaction_volume":"1"}
    response = client.post(
        api,
        json=data
    )
    
    time.sleep(1)
    
    user = db.query(models.User).filter(models.User.username == 'shuvra3').first()
    transaction = db.query(models.Transaction).filter().first()
    
    db.commit()
    stock = db.query(models.StockData).filter(models.StockData.ticker == 'GOOGLE').first()
    db.commit()
    user_stock = db.query(models.UserStockQuantity).filter(models.UserStockQuantity.user == user).first()

    assert (user.balance == 49800) and ( stock.available_quantity ==1999)
    
    
def test_transaction_by_userid():
    user = db.query(models.User).filter(models.User.username == 'shuvra3').first()
    api='/transactions/shuvra3'
    response = client.get(
        api,
    
    )
    assert len(response.json())==2
    
   
def test_transaction_by_timestamp():
    user = db.query(models.User).filter(models.User.username == 'shuvra3').first()
    transactions = db.query(models.Transaction).filter(models.Transaction.user == user).all()
    times = []
    for transaction in transactions:
       times.append(transaction.timestamp)
    min_time = min(times)
    middle_time = min_time + timedelta(seconds=1)
    current_time = datetime.now()
    start_time = middle_time.strftime('%Y-%m-%dT%H:%M:%S')
    end_time = current_time.strftime('%Y-%m-%dT%H:%M:%S')
    print('times:')
    print(times)
    print('middle time:')
    print(middle_time)
    print('end time:')
    print(end_time)
    
    api=f'/transactions/shuvra3/{start_time}/{end_time}'
    response = client.get(
        api,
    
    )
    print(response.json())
    assert len(response.json())==1
    
     
    
