from typing import Union
from pydantic import BaseModel
import json

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .tasks import *
from .database import SessionLocal, engine
from pydantic import BaseModel, ValidationError

models.Base.metadata.create_all(bind=engine)


class Payload(BaseModel):
    username: str = ""
    balance: float = 0.0


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TransactionPayload(BaseModel):
    user_id: str = ""
    ticker: str
    transaction_type: str
    transaction_volume: float


from fastapi import FastAPI

app = FastAPI()


# register a new user with a username and initial balance
@app.post("/users/")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if userid exists already
    if crud.userid_exists(db, user_id=user.user_id):
        raise HTTPException(status_code=400, detail="Userid already registered")
    # Check if username exists already
    if crud.username_exists(db, username=user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    crud.create_user(db=db, user=user)
    return {"status": "User created"}


@app.get("/users/{username}", response_model=schemas.User)
def read_user(username: str, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=400, detail="User not found")
    return db_user


@app.post("/stocks/")
def post_stock(stock: schemas.StockDataCreate, db: Session = Depends(get_db)):
    try:
        schemas.StockDataCreate(
            ticker=stock.ticker,
            open_price=stock.open_price,
            close_price=stock.close_price,
            high=stock.high,
            low=stock.low,
            volume=stock.volume,
            timestamp=stock.timestamp,
            available_quantity=stock.available_quantity,
            current_price=stock.current_price,
        )
    except ValidationError as e:
        return {"msg": e}

    response = crud.create_stock(db, stock=stock)
    return response


@app.get("/stocks/", response_model=list[schemas.StockData])
def read_stocks(db: Session = Depends(get_db)):
    db_stocks = crud.get_stocks(db)
    return db_stocks


@app.get("/stocks/{ticker}", response_model=schemas.StockData or None)
def get_stocks_by_ticker(ticker: str, db: Session = Depends(get_db)):
    db_stocks = crud.get_stocks_by_ticker(db, ticker)
    return db_stocks


@app.post("/transactions/")
def post_transaction(data: dict):
    create_transaction_task.delay(data)
    return {"msg": "Transaction started"}


"""    
@app.post("/transactions/")
def post_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    create_transaction_task.delay(db, transaction)
    #crud.create_transaction(db, transaction=transaction)
    return {"msg": "Transaction started"}
    #db_stock = crud.create_transaction(db, transaction=transaction)
    #return db_stock
"""


@app.get("/transactions/{user_id}", response_model=list[schemas.Transaction])
def get_transaction(user_id: str, db: Session = Depends(get_db)):
    db_transactions = crud.get_transactions(db, user_id=user_id)
    return db_transactions


@app.get(
    "/transactions/{user_id}/{start_timestamp}/{end_timestamp}",
    response_model=list[schemas.Transaction],
)
def get_transaction_by_time(
    user_id: str,
    start_timestamp: str,
    end_timestamp: str,
    db: Session = Depends(get_db),
):
    db_transactions = crud.get_transactions_by_time(
        db,
        user_id=user_id,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
    )
    return db_transactions


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.post("/test-task")
def test_celery():
    print("before task start...")
    add.delay()

    return {"msg": "Test celery"}
