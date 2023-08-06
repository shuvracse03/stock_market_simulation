from fastapi import FastAPI
from fastapi.testclient import TestClient
from .main import app
import json
from datetime import datetime

client = TestClient(app)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .main import app, get_db
from . import models
from .database import Base
import pytest

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()
        
app.dependency_overrides[get_db] = override_get_db     

@pytest.fixture()
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    
def test_server_running(test_db):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}
    
#Create new non-existing user
def test_create_user1(test_db):
    api='/users/'
    data = {"username":"shuvra2","user_id":"shuvra2","balance":"100000"}
    
    response = client.post(
        api,
        json=data
    )
    assert response.status_code == 200
    
    
#Attempt to create an existing user
def test_create_user2(test_db):
    api='/users/'
    data = {"username":"shuvra3","user_id":"shuvra3","balance":"100000"}
    
    response = client.post(
        api,
        json=data
    )
    response = client.post(
        api,
        json=data
    )
    assert response.status_code == 400
    
    
#Attempt to get an existing user's information
def test_get_user1(test_db):
    api_post='/users/'
    api_get='/users/shuvra3'
    
    data = {"username":"shuvra3","user_id":"shuvra3","balance":"100000"}
    
    response = client.post(
        api_post,
        json=data
    )
    response = client.get(
        api_get
    )
    assert response.status_code == 200
    
    
#Attempt to get an non-existing user's information
def test_get_user2(test_db):
   
    api_get='/users/shuvra4'
    
    response = client.get(
        api_get
    )
    assert response.status_code == 400

    
#Attempt to post a valid stock
def test_post_stock1(test_db):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {"ticker":"GOOGLE","open_price":"88","close_price":"91","high":"101","low":"81","volume":"0","current_price":"20","available_quantity":"20", "timestamp":current_time}
    api_post='/stocks/'
    
    response = client.post(
        api_post,
        json=data
    )
    assert response.status_code == 200
    
#Attempt to post an invalid stock, open price-> non number
def test_post_stock2(test_db):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {"ticker":"GOOGLE","open_price":"a88","close_price":"91","high":"101","low":"81","volume":"0","current_price":"20","available_quantity":"20", "timestamp":current_time}
    api_post='/stocks/'
    
    response = client.post(
        api_post,
        json=data
    ).json()
    assert response["detail"][0]['msg']=='value is not a valid float'
    
    
#Attempt to get stock list
def test_get_stock1(test_db):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data1 = {"ticker":"GOOGLE","open_price":"88","close_price":"91","high":"101","low":"81","volume":"0","current_price":"20","available_quantity":"20", "timestamp":current_time}
    data2 = {"ticker":"YAHOO","open_price":"18","close_price":"10","high":"80","low":"20","volume":"0","current_price":"10","available_quantity":"5", "timestamp":current_time}
    
    api_post='/stocks/'
    api_get='/stocks/'
    response = client.post(
        api_post,
        json=data1
    )
    response = client.post(
        api_post,
        json=data2
    )
    response = client.get(
        api_get
    )
    data_list = response.json()
    google_cnt=0
    yahoo_cnt=0
    for data in data_list:
       if data['ticker']=='YAHOO':
           yahoo_cnt+=1
       elif data['ticker']=='GOOGLE':
           google_cnt+=1
           
    assert yahoo_cnt == 1 
    assert google_cnt ==1
    
    
#Attempt to get stock for a ticker
def test_get_ticker_stock1(test_db):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data1 = {"ticker":"GOOGLE","open_price":"88","close_price":"91","high":"101","low":"81","volume":"0","current_price":"20","available_quantity":"20", "timestamp":current_time}
  
    api_post='/stocks/'
    api_get='/stocks/GOOGLE'
    response = client.post(
        api_post,
        json=data1
    )
    response = client.get(
        api_get
    )
    data = response.json()
    
    assert data['ticker']=='GOOGLE'
   
#Attempt to get stock for a ticker
def test_get_ticker_stock2(test_db):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data1 = {"ticker":"GOOGLE","open_price":"88","close_price":"91","high":"101","low":"81","volume":"0","current_price":"20","available_quantity":"20", "timestamp":current_time}
  
    api_post='/stocks/'
    api_get='/stocks/YAHOO'
    response = client.post(
        api_post,
        json=data1
    )
    response = client.get(
        api_get
    )
    data = response
    assert response.status_code == 204
    
   
    
    



