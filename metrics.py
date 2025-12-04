from prometheus_client import start_http_server, Gauge
import docker
import subprocess
import time
import psutil

# Configurações
CONTAINER_IMAGE = "giovanapr/is-person-detector:v1"  # imagem do container alvo
EXPORTER_PORT = 9100
SCRAPE_INTERVAL = 5.0  # segundos entre coletas

# Métricas Prometheus
cpu_usage_gauge = Gauge("container_cpu_usage_percent", "CPU usage (%)")
memory_usage_gauge = Gauge("container_memory_usage_mb", "Memory usage (MB)")
gpu_usage_gauge = Gauge("container_gpu_usage_percent", "GPU usage (%)")

client = docker.from_env()

def find_container_by_image(image_name):
    """
    Localiza um container pela imagem.
    """
    try:
        for c in client.containers.list(all=False):
            if any(image_name == tag or image_name in tag for tag in c.image.tags):
                return c
        return None
    except Exception as e:
        print("Erro ao listar containers:", e)
        return None

def get_container_stats_via_docker(container):
    """
    Retorna (cpu_percent, mem_mb) usando container.stats(stream=False),
    mesma fórmula do docker stats.
    """
    try:
        stats = container.stats(stream=False)

        # Memória
        mem_stats = stats.get("memory_stats", {})
        mem_usage = mem_stats.get("usage", 0)
        mem_mb = float(mem_usage) / 1024.0 / 1024.0

        # CPU %
        cpu_percent = 0.0
        cpu_stats = stats.get("cpu_stats", {})
        precpu_stats = stats.get("precpu_stats", {})

        cpu_total = cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
        precpu_total = precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
        cpu_delta = float(cpu_total) - float(precpu_total)

        system_cpu = cpu_stats.get("system_cpu_usage", 0)
        precpu_system = precpu_stats.get("system_cpu_usage", 0)
        system_delta = float(system_cpu) - float(precpu_system)

        percpu = cpu_stats.get("cpu_usage", {}).get("percpu_usage", None)
        num_cpus = len(percpu) if percpu else psutil.cpu_count(logical=True) or 1

        if system_delta > 0.0 and cpu_delta > 0.0:
            cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0
        else:
            cpu_percent = 0.0

        return cpu_percent, mem_mb

    except Exception as e:
        print("Erro ao coletar stats Docker:", e)
        return 0.0, 0.0

def get_gpu_usage():
    """
    Retorna % de uso da primeira GPU usando nvidia-smi.
    """
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            usage = int(result.stdout.strip().splitlines()[0])
            return usage
    except Exception as e:
        print("Erro ao coletar GPU:", e)
    return 0.0

def main():
    start_http_server(EXPORTER_PORT, addr="0.0.0.0")
    print(f"Exporter rodando em http://0.0.0.0:{EXPORTER_PORT}/metrics")

    while True:
        container = find_container_by_image(CONTAINER_IMAGE)
        if container is None:
            print("Container alvo não encontrado. Tentando novamente em 5s.")
            cpu_usage_gauge.set(0.0)
            memory_usage_gauge.set(0.0)
            gpu_usage_gauge.set(0.0)
            time.sleep(SCRAPE_INTERVAL)
            continue

        cpu_pct, mem_mb = get_container_stats_via_docker(container)
        gpu_pct = get_gpu_usage()

        # debug opcional
        print(f"[DEBUG] {container.name} CPU={cpu_pct:.2f}% MEM={mem_mb:.2f}MB GPU={gpu_pct:.1f}%")

        cpu_usage_gauge.set(cpu_pct)
        memory_usage_gauge.set(mem_mb)
        gpu_usage_gauge.set(gpu_pct)

        time.sleep(SCRAPE_INTERVAL)

if __name__ == "__main__":
    main()
