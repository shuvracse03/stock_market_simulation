from kafka import KafkaProducer
from time import sleep
from json import dumps
import random
import string
from datetime import datetime
import requests
import time

topic_name = 'StockTopic'

def generate_ticker(length):
    return ''.join(random.choices(string.ascii_uppercase, k=length))

price_range = (10,100)

def get_random_float(n_range):
   return random.uniform(n_range[0], n_range[1])
  
def get_random_int(n_range):
   return random.randint(n_range[0], n_range[1])
    
def initialize_tickers():
   tickers = []
   for i in range(10):
       ticker = generate_ticker(5)
       tickers.append(ticker)
   ticker_dict={}
   price_range = (10,100)
   qty_range = (10000,20000)
   for ticker in tickers:
      row ={'open_price':get_random_float(price_range), 'close_price':0, 'high':0, 'low':99999, 'volume':0, 'available_quantity': get_random_int(qty_range),'current_price':0, 'timestamp': datetime.now()}
      ticker_dict[ticker] = row
   return ticker_dict
   
def test_producer():
    producer = KafkaProducer(bootstrap_servers='localhost:29092', value_serializer=lambda x: dumps(x).encode('utf-8'))
    for e in range(100):
       data={'number':e}
       print(e)
       producer.send(topic_name, value=data)
       sleep(5)
     
def generate_radom_stock_data(ticker_dict):
     ticker, row = random.choice(list(ticker_dict.items()))
     current_price = get_random_float(price_range)
     ticker_dict[ticker]['high'] = max(current_price, ticker_dict[ticker]['high'])
     ticker_dict[ticker]['low'] = min(current_price, ticker_dict[ticker]['low'])
     ticker_dict[ticker]['current_price'] = current_price
     ticker_dict[ticker]['timestamp'] =  datetime.now()
     
     data_row={}
     data_row['ticker'] = ticker
     data_row = data_row | ticker_dict[ticker]
     data_row['timestamp']=data_row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
     return ticker_dict, data_row 
     
def main():
    ticker_dict = initialize_tickers()
    i=0
    #url = 'http://127.0.0.1:8001/stocks/'
    producer = KafkaProducer(bootstrap_servers='localhost:29092', value_serializer=lambda x: dumps(x).encode('utf-8'))
    NUMBER_OF_DATA =1000
    while i< 1000:
        ticker_dict, data_row = generate_radom_stock_data(ticker_dict)
        producer.send(topic_name, value=data_row)
        print(data_row)
        i+=1
        time.sleep(0.5)
        
if __name__==main():
   main()
