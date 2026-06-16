from exporter import export_to_excel
from scanner import scan_network

import subprocess
import socket
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.table import Table

console = Console()
results = []

vlans = {
    "150": "10.101.150.",
    "110": "10.101.110.",
    "118": "10.101.118.",
    "113": "10.101.113."
}

console.print("[cyan]Available VLANs:[/cyan]")

for vlan in vlans:
    console.print(f" - {vlan}")

console.print(" - ALL")

selected_vlan = input("Select VLAN: ")

if selected_vlan not in vlans and selected_vlan.upper() != "ALL":
    console.print("[red]Invalid VLAN[/red]")
    exit()

if selected_vlan.upper() != "ALL":
    network = vlans[selected_vlan]

if selected_vlan.upper() == "ALL":
    results = []

    for vlan_name, network in vlans.items():
        console.print(f"[yellow]Scanning VLAN {vlan_name}[/yellow]")

        vlan_results = scan_network(network)

        for row in vlan_results:
            results.append(row)

    selected_vlan = "ALL"
console.print("[cyan]Scanning network...[/cyan]")

if selected_vlan.upper() != "ALL":
    results = scan_network(network)

table = Table(title=f"VLAN {selected_vlan} Scan")

table.add_column("IP", style="cyan")
table.add_column("Hostname", style="green")
table.add_column("Ping", style="yellow")
table.add_column("Status")

for ip, host, ping_ms, status in results:

    if status == "ONLINE":
        status_color = "[green]ONLINE[/green]"
    else:
        status_color = "[red]OFFLINE[/red]"

    table.add_row(ip, host, ping_ms, status_color)

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
