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


def _get_mac_arp(ip: str) -> str:
    """Быстрый — ARP (только тот же VLAN)."""
    try:
        arp = subprocess.run(
            ["arp", "-a", ip],
            capture_output=True, text=True, timeout=2)
        match = re.search(
            r"([0-9a-fA-F]{2}[:\-]){5}[0-9a-fA-F]{2}",
            arp.stdout)
        if match:
            return match.group(0).upper().replace("-", ":")
    except Exception:
        pass
    return None


def _get_mac_psexec(ip: str) -> str:
    """Fallback — psexec ipconfig /all (работает между VLANами, медленно)."""
    try:
        result = subprocess.run(
            ["psexec", f"\\\\{ip}", "-s", "-n", "3",
             "ipconfig", "/all"],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace"
        )
        output = result.stdout + result.stderr

        # Physical Address. . . . . . . . . : 4C-CC-6A-50-81-60
        matches = re.findall(
            r"Physical Address[\s\.]+:\s*([0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2})",
            output
        )
        for mac in matches:
            mac_clean = mac.upper().replace("-", ":")
            if mac_clean != "00:00:00:00:00:00":
                return mac_clean
    except Exception:
        pass
    return "N/A"


def _get_mac(ip: str, fetch_mac: bool) -> str:
    if not fetch_mac:
        return "N/A"
    # сначала быстрый ARP
    mac = _get_mac_arp(ip)
    if mac:
        return mac
    # fallback через psexec
    return _get_mac_psexec(ip)


def check_host(ip: str, results: list, callback=None,
               stop_flag=None, fetch_mac: bool = False) -> None:
    if stop_flag and stop_flag.is_set():
        if callback:
            callback()
        return

    try:
        ping = subprocess.run(
            ["ping", "-n", "1", "-w", "500", ip],
            capture_output=True, text=True)

        if ping.returncode == 0:
            ping_ms = _parse_ping_ms(ping.stdout)

            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except (socket.herror, socket.gaierror):
                hostname = "N/A"

            mac = _get_mac(ip, fetch_mac)

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


def scan_network(network: str, progress_callback=None,
                 stop_flag=None, fetch_mac: bool = False) -> list:
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
                stop_flag,
                fetch_mac
            )

    results.sort(key=lambda x: list(map(int, x[0].split("."))))
    return results