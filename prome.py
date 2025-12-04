import requests
import pika
import json
import time

# Configurações
METRICS_URL = "http://10.10.2.1:9100/metrics"  # endpoint Prometheus
SCRAPE_INTERVAL = 5.0  # segundos entre coletas

# Configurações RabbitMQ
RABBITMQ_HOST = "10.10.2.1"
RABBITMQ_PORT = 5672
RABBITMQ_USER = "gustavofb"
RABBITMQ_PASS = "freitas213"
EXCHANGE_NAME = "prometheus_logs_exchange"  # exchange fanout

def connect_rabbitmq():
    """Conecta ao RabbitMQ e cria o exchange fanout."""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=30
    )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    #  Declara um exchange do tipo fanout (envia para todos os consumidores)
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="fanout", durable=True)
    return connection, channel

def parse_metrics(text):
    """Lê o texto Prometheus e extrai as métricas desejadas."""
    cpu = mem = gpu = 0.0
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        if line.startswith("container_cpu_usage_percent"):
            try:
                cpu = float(line.split()[-1])
            except:
                pass
        elif line.startswith("container_memory_usage_mb"):
            try:
                mem = float(line.split()[-1])
            except:
                pass
        elif line.startswith("container_gpu_usage_percent"):
            try:
                gpu = float(line.split()[-1])
            except:
                pass
    return cpu, mem, gpu

def main():
    connection, channel = connect_rabbitmq()
    print(f"Coletor iniciado — enviando métricas de {METRICS_URL} para o exchange '{EXCHANGE_NAME}'")

    try:
        while True:
            try:
                resp = requests.get(METRICS_URL, timeout=5)
                if resp.status_code == 200:
                    cpu, mem, gpu = parse_metrics(resp.text)
                    timestamp_us = int(time.time() * 1_000_000)  # microssegundos epoch

                    payload = {
                        "container_cpu_usage_percent": cpu,
                        "container_memory_usage_mb": mem,
                        "container_gpu_usage_percent": gpu,
                        "timestamp": timestamp_us
                    }

                    # Envia para o exchange fanout (sem routing_key)
                    channel.basic_publish(
                        exchange=EXCHANGE_NAME,
                        routing_key="",
                        body=json.dumps(payload),
                        properties=pika.BasicProperties(delivery_mode=2)
                    )
                    print("[RABBITMQ] Enviado:", payload)
                else:
                    print("Falha ao obter métricas HTTP:", resp.status_code)

            except Exception as e:
                print("Erro ao coletar/enviar métricas:", e)

            time.sleep(SCRAPE_INTERVAL)

    finally:
        print("Encerrando conexão RabbitMQ...")
        connection.close()

if __name__ == "__main__":
    main()
