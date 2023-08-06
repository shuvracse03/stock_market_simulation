from kafka import KafkaConsumer
import requests

topic_name = "StockTopic"
import json


def main():
    consumer = KafkaConsumer(
        topic_name, group_id="my-group", bootstrap_servers=["localhost:29092"]
    )
    stock_update_url = "http://127.0.0.1:8001/stocks/"
    for msg in consumer:
        data_row = json.loads(msg.value)
        x = requests.post(
            stock_update_url, json=data_row
        )  # Send request to API for stock update
        print(x.text)


if __name__ == main():
    main()
