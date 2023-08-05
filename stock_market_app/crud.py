from sqlalchemy.orm import Session
from fastapi import  HTTPException
from datetime import datetime
from . import models, schemas
from sqlalchemy import and_
import redis
import json
from pydantic.tools import parse_obj_as

redis_client = redis.Redis(
    host='redis',
    port=6379,
    charset="utf-8",
    decode_responses=True
    )
    
CACHE_TIMEOUT=120
def get_user_by_username(db: Session, username: str):
    #redis_client.set(username, "value2")
    # Try fetching user data from Redis cache
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
       record.volume = stock.volume
       record.timestamp =stock.timestamp
       record.current_price = stock.current_price
       record.available_quantity = stock.available_quantity
       db.commit()
       
       return record
    
    
    
    
def get_stocks(db: Session):
    return db.query(models.StockData).all()
    
def get_stocks_by_ticker(db: Session, ticker: str):
    return db.query(models.StockData).filter(models.StockData.ticker == ticker).first()
    
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
    #create transaction
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
        
    return db_transaction
    


