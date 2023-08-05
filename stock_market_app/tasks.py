from celery import Celery
import time



BROKER="redis://redis:6379"

app = Celery("stock_market", backend="rpc://", broker=BROKER)

@app.task
def add():
    print('celery task started')
    for i in range(0,20):
        print('i:',i)
        time.sleep(1)
    return 3+4
