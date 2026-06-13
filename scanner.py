import subprocess
import socket


def check_host(ip, results):
    try:
        ping = subprocess.run(
            ["ping", "-n", "1", "-w", "300", ip],
            capture_output=True,
            text=True
        )

        ping_ms = "-"

        if ping.returncode == 0:

            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except:
                hostname = "N/A"

            results.append((ip, hostname, ping_ms, "ONLINE"))

        else:
            results.append((ip, "N/A", "-", "OFFLINE"))

    except Exception:
        pass



from concurrent.futures import ThreadPoolExecutor


def scan_network(network):
    results = []

    with ThreadPoolExecutor(max_workers=100) as executor:
        for i in range(1, 255):
            executor.submit(
                check_host,
                f"{network}{i}",
                results
            )

    results.sort(
        key=lambda x: list(map(int, x[0].split(".")))
    )

    return results
