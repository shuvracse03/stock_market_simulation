from fastapi import FastAPI
from fastapi.testclient import TestClient
from .main import *
from . import models
import time

import json
from datetime import datetime
from .database import SessionLocal, engine

db = SessionLocal()
client = TestClient(app)


def test_create_transaction_task():
    user = db.query(models.User).filter(models.User.username == "shuvra3").first()
    if user is not None:
        db.query(models.UserStockQuantity).filter(
            models.UserStockQuantity.user == user
        ).delete()
        db.query(models.Transaction).filter(models.Transaction.user == user).delete()
        db.query(models.User).filter(models.User.username == "shuvra3").delete()
        db.commit()

    api = "/users/"
    data = {"username": "shuvra3", "user_id": "shuvra3", "balance": "50000"}

    response = client.post(api, json=data)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    stock_data = db.query(models.StockData).filter(models.StockData.ticker == "GOOGLE")

    if stock_data is not None:
        stock_data.delete()
        db.commit()

    data1 = {
        "ticker": "GOOGLE",
        "open_price": "88",
        "close_price": "91",
        "high": "101",
        "low": "81",
        "volume": "0",
        "current_price": "200",
        "available_quantity": "2000",
        "timestamp": current_time,
    }
    # create stock
    api = "/stocks/"
    response = client.post(api, json=data1)
    time.sleep(0.5)
    data = {
        "user_id": "shuvra3",
        "ticker": "GOOGLE",
        "transaction_type": "BUY",
        "transaction_volume": "2",
    }
    create_transaction_task.delay(data)
    time.sleep(1)
    user = db.query(models.User).filter(models.User.username == "shuvra3").first()
    assert user.balance == 49600
