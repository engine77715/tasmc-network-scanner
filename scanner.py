import subprocess
import socket
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

_lock = threading.Lock()

# ── скрытие консольных окон дочерних процессов ────────────────────────────────
# Критично для PyInstaller --windowed exe: без этого флага каждый
# subprocess.run() на короткое время мелькает черным окном cmd,
# а при 100+ параллельных потоках это выглядит как "луп" открывающихся окон.
if sys.platform == "win32":
    _CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW
    _STARTUPINFO = subprocess.STARTUPINFO()
    _STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    _STARTUPINFO.wShowWindow = subprocess.SW_HIDE
else:
    _CREATE_NO_WINDOW = 0
    _STARTUPINFO = None


def _run_hidden(cmd, timeout=None, encoding=None, errors=None):
    """subprocess.run с полностью скрытым окном консоли."""
    kwargs = dict(
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=_CREATE_NO_WINDOW,
    )
    if _STARTUPINFO is not None:
        kwargs["startupinfo"] = _STARTUPINFO
    if encoding:
        kwargs["encoding"] = encoding
    if errors:
        kwargs["errors"] = errors
    return subprocess.run(cmd, **kwargs)


def _parse_ping_ms(output: str) -> str:
    match = re.search(r"[Tt]ime[=<](\d+)\s*ms", output)
    if match:
        return f"{match.group(1)} ms"
    return "-"


def _get_mac_arp(ip: str) -> str:
    """Быстрый — ARP (только тот же VLAN)."""
    try:
        arp = _run_hidden(["arp", "-a", ip], timeout=2)
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
        result = _run_hidden(
            ["psexec", f"\\\\{ip}", "-s", "-n", "3",
             "ipconfig", "/all"],
            timeout=15, encoding="utf-8", errors="replace"
        )
        output = result.stdout + result.stderr

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
    mac = _get_mac_arp(ip)
    if mac:
        return mac
    return _get_mac_psexec(ip)


def check_host(ip: str, results: list, callback=None,
               stop_flag=None, fetch_mac: bool = False) -> None:
    if stop_flag and stop_flag.is_set():
        if callback:
            callback()
        return

    try:
        ping = _run_hidden(["ping", "-n", "1", "-w", "500", ip])

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