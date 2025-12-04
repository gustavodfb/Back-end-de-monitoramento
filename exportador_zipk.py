import requests
import json
import pika
import time
from collections import deque

# Configuração do Zipkin e RabbitMQ
ZIPKIN_URL = "http://10.10.2.211:30200/zipkin/api/v2/traces?serviceName=person.detector&limit=10"
RABBITMQ_HOST = "10.10.2.1"
RABBITMQ_PORT = 5672
RABBITMQ_USER = "gustavofb"
RABBITMQ_PASS = "freitas213"
EXCHANGE_NAME = "zipkin_logs_exchange"  # exchange fanout

def connect_rabbitmq():
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST, 5672))
    channel = connection.channel()
    # Declara um exchange do tipo fanout
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="fanout", durable=True)
    return connection, channel

def get_traces():
    response = requests.get(ZIPKIN_URL)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao obter logs: {response.status_code}")
        return []

def filter_spans(traces, service_name="person.detector", span_name="detection_and_render"):
    filtered = []
    for trace in traces:
        spans_filtered = [
            span for span in trace
            if span.get("localEndpoint", {}).get("serviceName") == service_name
            and span.get("name") == span_name
        ]
        if spans_filtered:
            filtered.append(spans_filtered)
    return filtered

# Deque para armazenar apenas os últimos 100 IDs enviados
sent_ids = deque(maxlen=100)

def publish_logs(channel, traces):
    count = 0
    for trace in traces:
        for span in trace:
            span_id = span.get("id")
            if span_id and span_id not in sent_ids:
                message = json.dumps(span)
                # Publica no exchange fanout (sem routing_key)
                channel.basic_publish(
                    exchange=EXCHANGE_NAME,
                    routing_key="",
                    body=message,
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                sent_ids.append(span_id)
                count += 1
    if count > 0:
        print(f"Enviados {count} spans novos para o exchange '{EXCHANGE_NAME}'")
    else:
        print("Nenhum novo span encontrado")

def main():
    connection, channel = connect_rabbitmq()
    try:
        while True:
            traces = get_traces()
            filtered_traces = filter_spans(traces)
            if filtered_traces:
                publish_logs(channel, filtered_traces)
            time.sleep(10)
    except KeyboardInterrupt:
        print("Encerrando...")
        connection.close()

if __name__ == "__main__":
    main()
