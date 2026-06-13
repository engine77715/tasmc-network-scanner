from exporter import export_to_excel
from scanner import scan_network

import subprocess
import socket
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.table import Table

console = Console()
results = []




network = "10.101.150."

console.print("[cyan]Scanning network...[/cyan]")

results = scan_network(network)

table = Table(title="VLAN 150 Scan")

table.add_column("IP", style="cyan")
table.add_column("Hostname", style="green")
table.add_column("Ping", style="yellow")
table.add_column("Status")

for ip, host, ping_ms, status in results:
    table.add_row(ip, host, ping_ms, status)

console.print(table)

online_count = sum(1 for r in results if r[3] == "ONLINE")
offline_count = sum(1 for r in results if r[3] == "OFFLINE")

console.print(f"[green]ONLINE:[/green] {online_count}")
console.print(f"[red]OFFLINE:[/red] {offline_count}")
console.print(f"[cyan]TOTAL:[/cyan] {len(results)}")
console.print(f"[yellow]Found hosts: {len(results)}[/yellow]")

file = export_to_excel(results)

console.print(
    f"[green]Excel saved:[/green] {file}"
)
