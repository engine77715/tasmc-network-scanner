# TASMC Network Scanner

IT tool for Ichilov Hospital (tasmc.corp) network management.

## Features
- Scan VLANs 150 / 110 / 118 / 113 or ALL at once
- Host details window with 6 tabs:
  - **Info** — IP, Hostname, Ping, Status, MAC, Logged-in User
  - **Printers** — list of installed printers
  - **System** — OS, Last Boot, Model, Serial, Disk usage
  - **Services** — running/stopped services with filter
  - **Software** — installed programs list
  - **Power** — Remote Reboot / Shutdown
- Remote actions: RDP, PsExec, Net Use, UNC, Comp Mgmt, Event Log
- Unjoin Domain with credentials dialog
- Export results to Excel (with MAC column)
- Dark / Light theme toggle
- Stop scan at any time

## Requirements
- Python 3.10+
- Windows only (uses wmic, mstsc, ping, arp)
- psexec in PATH for PsExec button

## Install
```
pip install -r requirements.txt
```

## Run
```
python main.py
```

## Project Structure
```
tasmc-network-scanner/
├── main.py          — entry point
├── gui.py           — main GUI (tkinter)
├── scanner.py       — network scanning (ping + ARP + DNS)
├── exporter.py      — Excel export (openpyxl)
├── config.py        — settings and constants
├── requirements.txt
└── README.md
```

## Network
| VLAN | Subnet         |
|------|----------------|
| 150  | 10.101.150.x   |
| 110  | 10.101.110.x   |
| 118  | 10.101.118.x   |
| 113  | 10.101.113.x   |