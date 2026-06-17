import subprocess
import socket
import re
import threading
from concurrent.futures import ThreadPoolExecutor

_lock = threading.Lock()


def _parse_ping_ms(output: str) -> str:
    match = re.search(r"[Tt]ime[=<](\d+)\s*ms", output)
    if match:
        return f"{match.group(1)} ms"
    return "-"


def _get_mac(ip: str) -> str:
    try:
        arp = subprocess.run(
            ["arp", "-a", ip],
            capture_output=True,
            text=True
        )
        match = re.search(
            r"([0-9a-fA-F]{2}[-:]){5}[0-9a-fA-F]{2}",
            arp.stdout
        )
        if match:
            return match.group(0).upper()
        return "N/A"
    except Exception:
        return "N/A"


def check_host(ip: str, results: list, callback=None, stop_flag=None) -> None:
    if stop_flag and stop_flag.is_set():
        if callback:
            callback()
        return

    try:
        ping = subprocess.run(
            ["ping", "-n", "1", "-w", "500", ip],
            capture_output=True,
            text=True
        )

        if ping.returncode == 0:
            ping_ms = _parse_ping_ms(ping.stdout)

            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except (socket.herror, socket.gaierror):
                hostname = "N/A"

            mac = _get_mac(ip)

            with _lock:
                results.append((ip, hostname, ping_ms, "ONLINE", mac))
        else:
            with _lock:
                results.append((ip, "N/A", "-", "OFFLINE", "N/A"))

    except Exception:
        with _lock:
            results.append((ip, "N/A", "-", "OFFLINE", "N/A"))

    finally:
        if callback:
            callback()


def scan_network(network: str, progress_callback=None, stop_flag=None) -> list:
    results = []

    with ThreadPoolExecutor(max_workers=100) as executor:
        for i in range(1, 255):
            if stop_flag and stop_flag.is_set():
                break
            executor.submit(
                check_host,
                f"{network}{i}",
                results,
                progress_callback,
                stop_flag
            )

    results.sort(key=lambda x: list(map(int, x[0].split("."))))
    return results