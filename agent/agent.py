"""Agente local de métricas (host/VM). Não lê VMs vizinhas e não recolhe conteúdo pessoal."""
from __future__ import annotations

import argparse
import logging
import os
import platform
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx
import psutil
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name('.env'))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("edu-infra-agent")


def configuration():
    url = os.getenv("EDU_API_URL", "").rstrip("/")
    token = os.getenv("EDU_AGENT_TOKEN", "")
    computer_id = int(os.getenv("EDU_COMPUTER_ID", "0"))
    interval = max(10, int(os.getenv("EDU_INTERVAL_SECONDS", "60")))
    disk = os.getenv("EDU_DISK_PATH") or ("C:\\" if os.name == 'nt' else "/")
    parsed = urlparse(url)
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}):
        raise ValueError("EDU_API_URL deve usar HTTPS, exceto HTTP loopback no mesmo computador")
    if computer_id < 1 or not token.startswith("eia_"):
        raise ValueError("Configure EDU_COMPUTER_ID e EDU_AGENT_TOKEN da máquina cadastrada")
    return url, computer_id, token, interval, disk


def collect(disk_path: str):
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage(disk_path).percent,
        "uptime_seconds": max(0, time.time() - psutil.boot_time()),
        "os_name": f"{platform.system()} {platform.release()}"[:180],
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


def send(client: httpx.Client, url: str, computer_id: int, token: str, metric: dict):
    response = client.post(url + "/api/agent/metrics", json=metric, headers={"X-Computer-ID": str(computer_id), "X-Agent-Token": token})
    response.raise_for_status()
    return response.json()


def run(once: bool = False):
    url, computer_id, token, interval, disk_path = configuration()
    log.info("Agente iniciado: computador=%d, intervalo=%ds, destino=%s", computer_id, interval, url)
    with httpx.Client(timeout=15, follow_redirects=False) as client:
        while True:
            start = time.monotonic()
            try:
                metric = collect(disk_path)
                answer = send(client, url, computer_id, token, metric)
                log.info("Coleta recebida: id=%s CPU=%.1f%% RAM=%.1f%% Disco=%.1f%%", answer.get("id"), metric["cpu_percent"], metric["memory_percent"], metric["disk_percent"])
            except (httpx.HTTPError, OSError, ValueError) as exc:
                log.error("Falha na coleta/envio: %s", exc)
                if once:
                    raise SystemExit(1) from exc
            if once:
                return
            time.sleep(max(0, interval - (time.monotonic() - start)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='EDU-Infra Analytics: coleta apenas a máquina local')
    parser.add_argument('--once', action='store_true', help='Uma única coleta e envio')
    arguments = parser.parse_args()
    try:
        run(arguments.once)
    except KeyboardInterrupt:
        log.info("Agente encerrado pelo operador")
