from openpyxl import Workbook
from datetime import datetime
import os


def export_to_excel(results):
    if not os.path.exists("exports"):
        os.makedirs("exports")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    filename = f"exports/VLAN150_{timestamp}.xlsx"

    wb = Workbook()
    ws = wb.active

    ws.title = "Scan Results"
    ws.append([
        "IP",
        "Hostname",
        "Ping",
        "Status"
    ])

    for row in results:
        ws.append(row)

    wb.save(filename)

    return filename
