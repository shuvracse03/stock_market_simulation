## Stock market simulation using FastAPI, Redis, Celery, Flower, Kafka

### How to run?

```
./linux_script.sh --build
```

### Data Model
We have used 4 Database tables for SQLAlchemy.

    - User: Fields are user_id, username, balance, transactions, user_stock_quantities
    - UserStockQuantity: Fields are ticker, quantity, owner_id. This table was necessary to keep track of user’s stocks bought. This was needed to check validity of selling a stock. For example, if there is a sell transaction order for ticker: ‘GOOGL’, ‘volume’:100, I had checked if the user has at least this amount of stock for this ticker.
    - StockData: Fields are ticker, open_price, close_price, high, low, volume, available_quantity, current_price, timestamp
    - Transaction: Fields are transaction_id, ticker, transaction_type, transaction_volume, transaction_price, timestamp, owner_id

### Celery Task Queue

I have defined 4 celery workers in docker.  Adding more workers enables to\
scale up the processing power to handle higher loads without modifying the\
 individual workers. Also, if one worker fails, other workers still help to\
  run the tasks. I have also added concurrency=8 for each of them. Single\
   queue was used. I could have also used queues/per worker.

### Redis 
I have also created a Redis container named redis in docker compose.\
 Redis has been used as broker for Celery and Flower. Also, I used Redis to\
  cache the data for different APIs. I had set 2 minutes for cache time out.\
  A few apis, checked in the cache first. In case of cache miss, query was made to database.

### Kafka
 The code for stock data generation is in kafka_producer.py file.\
  I generated 10 random ticker names. First of all, I initialized \
  single rows for each of the ticker with random prices(range 10-100) and\
   available quantity range(10000-20000).\
   After each 0.5 secs, I generated a new stock data row by\
    choosing a random ticker and updated a random current_price\
     value[also updated high, low accordignly]. The Kafka producer\
      was sending this data to StockTopic each 0.5 secs. I ran it for\
       1000 times.

In another script kafka_consumer.py, I read the data from StockTopic\
 and parsed to json. Every time, the consumer got a data row, it made\
  a post API call to update the stock data.  I have created one container\
   kafka, with port 29002. It is also possible to make more brokers easily.\
    I had avoided as I had already made lots of containers and it was taking\
     much resources in my machine.
