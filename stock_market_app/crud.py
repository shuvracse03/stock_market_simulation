from sqlalchemy.orm import Session
from fastapi import  HTTPException
from datetime import datetime
from . import models, schemas
from .tasks import *
from sqlalchemy import and_
import redis
import json
from pydantic.tools import parse_obj_as
from pydantic.json import pydantic_encoder

redis_client = redis.Redis(
    host='redis',
    port=6379,
    charset="utf-8",
    decode_responses=True
    )
    
CACHE_TIMEOUT=120
def get_user_by_username(db: Session, username: str):
    cached_data = redis_client.get(username)
    if cached_data:
       print('found in cache')
       user_dict = json.loads(cached_data)
       user = parse_obj_as(schemas.User, user_dict)
       return user
    else:
       print('Cache missed. Hit database')
       result=  db.query(models.User).filter(models.User.username == username).first()
       pyd_model= schemas.User(user_id= result.user_id, username=result.username, balance=result.balance, transactions=result.transactions)
       
       serialized_data = json.dumps(pyd_model.dict())
       redis_client.setex(username, CACHE_TIMEOUT, serialized_data)
       
       return result



def create_user(db: Session, user: schemas.UserCreate):
    #if this user id or user name does not exist then create, or return none
    
    db_user = models.User(user_id=user.user_id, username=user.username, balance=user.balance)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
    
    

def create_stock(db: Session, stock: schemas.StockDataCreate):
    #create stock
    result = db.query(models.StockData).filter(models.StockData.ticker == stock.ticker)
    if result.first() is None:
       
       db_stock = models.StockData(ticker=stock.ticker, open_price= stock.open_price, close_price=stock.close_price,\
     high=stock.high, low=stock.low, volume=stock.volume, timestamp= stock.timestamp, available_quantity= stock.available_quantity, current_price=stock.current_price)
       db.add(db_stock)
       db.commit()
       db.refresh(db_stock)
       return db_stock
    else:     
       record = result.one()
 
       record.open_price =stock.open_price
       record.close_price = stock.close_price
       record.high = stock.high
       record.low = stock.low
       #record.volume = stock.volume
       record.timestamp =stock.timestamp
       record.current_price = stock.current_price
       #record.available_quantity = stock.available_quantity
       db.commit()
       
       return record
    
    
    
    
def get_stocks(db: Session):
    cache_key = 'stocks'
    cached_data = redis_client.get(cache_key)
    if cached_data:
       print('found in cache')
       stock_dict = json.loads(cached_data)
       print(stock_dict)
       stocks = parse_obj_as(list[schemas.StockData], stock_dict)
       return stocks
    else:
       print('missed cache')
       result =  db.query(models.StockData).all()
       pyd_models=[]
       for d in result:
           pyd_model= schemas.StockData(id = d.id, ticker=d.ticker, open_price=d.open_price,\
           close_price=d.close_price, high=d.high, low=d.low, volume=d.volume,\
           available_quantity=d.available_quantity, current_price=d.current_price, timestamp=d.timestamp)
           pyd_models.append(pyd_model)
       
       serialized_data = json.dumps(pyd_models, default=pydantic_encoder)#datetime conversion needs str
       print('serialized data')
       print(serialized_data)
       redis_client.setex(cache_key, CACHE_TIMEOUT, serialized_data)
       return result    
         
def get_stocks_by_ticker(db: Session, ticker: str):
    cache_key = 'stock-'+ticker
    cached_data = redis_client.get(cache_key)
    if cached_data:
       print('found in cache')
       stock_ticker_dict = json.loads(cached_data)
       stock_ticker = parse_obj_as(schemas.StockData, stock_ticker_dict)
       return stock_ticker
    else:  
       print('cache miss')
       result = db.query(models.StockData).filter(models.StockData.ticker == ticker).first()
       pyd_model= schemas.StockData(id = result.id, ticker=result.ticker, open_price=result.open_price,\
        close_price=result.close_price, high=result.high, low=result.low, volume=result.volume,\
         available_quantity=result.available_quantity, current_price=result.current_price, timestamp=result.timestamp)
       
       serialized_data = json.dumps(pyd_model.dict(), default=str)#datetime conversion needs str

       redis_client.setex(cache_key, CACHE_TIMEOUT, serialized_data)
       return result
    
def get_transactions(db: Session, user_id: str):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user is None:
       raise HTTPException(status_code=400, detail="User does not exist")
    return db.query(models.Transaction).filter(models.Transaction.owner_id == user.id).all()
    

    
def get_transactions_by_time(db: Session, user_id: str, start_timestamp:str, end_timestamp:str):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user is None:
       raise HTTPException(status_code=400, detail="User does not exist") 
    start_time =  datetime.strptime(start_timestamp, '%Y-%m-%dT%H:%M:%S')
    end_time = datetime.strptime(end_timestamp, '%Y-%m-%dT%H:%M:%S')
    print(start_time)
    print(end_time)
    return db.query(models.Transaction).filter(and_( (models.Transaction.owner_id==user.id), (models.Transaction.timestamp >= start_time), (models.Transaction.timestamp <= end_time) )).all()
    
'''
User stock volume update
Stock data's volume update
User's balance updated
Transaction new entry created
'''

def create_transaction(db: Session, transaction: schemas.TransactionCreate):
    create_transaction_task(db, transaction).delay() #send to celery task
    
    
    


