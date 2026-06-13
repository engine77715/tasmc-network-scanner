from exporter import export_to_excel

import subprocess
import socket
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.table import Table

console = Console()
results = []


def check_host(ip):
    try:
        ping = subprocess.run(
            ["ping", "-n", "1", "-w", "300", ip],
            capture_output=True,
            text=True
        )

        if ping.returncode == 0:
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except:
                hostname = "N/A"

            results.append((ip, hostname, "ONLINE"))

    except Exception:
        pass


network = "10.101.150."

console.print("[cyan]Scanning network...[/cyan]")

with ThreadPoolExecutor(max_workers=100) as executor:
    for i in range(1, 255):
        executor.submit(check_host, f"{network}{i}")

results.sort(key=lambda x: list(map(int, x[0].split("."))))

table = Table(title="VLAN 150 Scan")

table.add_column("IP", style="cyan")
table.add_column("Hostname", style="green")
table.add_column("Status", style="bold green")

for ip, host, status in results:
    table.add_row(ip, host, status)

console.print(table)
console.print(f"[yellow]Found hosts: {len(results)}[/yellow]")

file = export_to_excel(results)

console.print(
    f"[green]Excel saved:[/green] {file}"
)