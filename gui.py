import tkinter as tk
from tkinter import ttk
import threading
from scanner import scan_network
from exporter import export_to_excel

root = tk.Tk()
root.configure(bg="#f5f5f5")

root.title("TASMC Network Scanner")
root.geometry("900x600")

title_label = tk.Label(
    root,
    text="TASMC Network Scanner",
    font=("Segoe UI", 20, "bold")
)
title_label.pack(pady=10)

vlan_frame = tk.Frame(root)
vlan_frame.pack(pady=10)

tk.Label(vlan_frame, text="VLAN:").pack(side="left")

vlan_combo = ttk.Combobox(
    vlan_frame,
    values=["150", "110", "118", "113", "ALL"],
    state="readonly",
    width=15
)

vlan_combo.set("150")
vlan_combo.pack(side="left", padx=10)


def sort_column(col, reverse):
    data = [
        (tree.set(item, col), item)
        for item in tree.get_children("")
    ]

    data.sort(reverse=reverse)

    for index, (_, item) in enumerate(data):
        tree.move(item, "", index)

    tree.heading(
        col,
        command=lambda: sort_column(
            col,
            not reverse
        )
    )


def search_results(event=None):
    search_text = search_entry.get().lower()

    for item in tree.get_children():

        values = tree.item(item)["values"]

        ip = str(values[0]).lower()
        hostname = str(values[1]).lower()

        if search_text in ip or search_text in hostname:
            tree.selection_set(item)
            tree.focus(item)
            tree.see(item)
            break

def show_host_info(event):

    selected = tree.focus()

    if not selected:
        return

    values = tree.item(selected)["values"]

    ip = values[0]
    hostname = values[1]
    ping = values[2]
    status = values[3]

    info_window = tk.Toplevel(root)

    info_window.title("Host Information")
    info_window.geometry("400x250")

    tk.Label(
        info_window,
        text=f"IP: {ip}"
    ).pack(pady=10)

    tk.Label(
        info_window,
        text=f"Hostname: {hostname}"
    ).pack(pady=10)

    tk.Label(
        info_window,
        text=f"Ping: {ping}"
    ).pack(pady=10)

    tk.Label(
        info_window,
        text=f"Status: {status}"
    ).pack(pady=10)
def start_scan():
    threading.Thread(
        target=run_scan,
        daemon=True
    ).start()


def run_scan():
    selected_vlan = vlan_combo.get()
    status_label.config(text="Scanning...")
    scan_button.config(state="disabled")
    progress.start(10)
    root.update()

    progress.start(10)

    vlans = {
        "150": "10.101.150.",
        "110": "10.101.110.",
        "118": "10.101.118.",
        "113": "10.101.113."
    }

    network = vlans[selected_vlan]
    scan_button.config(state="disabled")
    status_label.config(text="Scanning...")
    results = scan_network(network)

    online_count = sum(1 for r in results if r[3] == "ONLINE")
    offline_count = sum(1 for r in results if r[3] == "OFFLINE")

    online_label.config(
        text=f"🟢 ONLINE: {online_count}"
    )

    offline_label.config(
        text=f"🔴 OFFLINE: {offline_count}"
    )

    for item in tree.get_children():
        tree.delete(item)

    for ip, host, ping, status in results:
        if status == "ONLINE":
            tree.insert("", "end",
                        values=(ip, host, ping, status),
                        tags=("online",))
        else:
            tree.insert("", "end",
                        values=(ip, host, ping, status),
                        tags=("offline",))
    progress.stop()

    scan_button.config(state="normal")

    status_label.config(
        text=f"Completed - Found {len(results)} hosts"
    )
    print(f"Found {len(results)} hosts")

    status_label.config(
        text=f"Scan completed. Found {len(results)} hosts"
    )


scan_button = tk.Button(
    root,
    text="Start Scan",
    width=20,
    command=start_scan
)

scan_button.pack(pady=10)


def export_results():
    export_to_excel(results)


export_button = tk.Button(
    root,
    text="Export Excel",
    width=20,
    command=export_results
)

export_button.pack(pady=5)
online_label = tk.Label(root, text="ONLINE: 0")
online_label.pack()

offline_label = tk.Label(root, text="OFFLINE: 0")
offline_label.pack()
search_frame = tk.Frame(root)
search_frame.pack(pady=5)

tk.Label(
    search_frame,
    text="Search:"
).pack(side="left")

search_entry = tk.Entry(
    search_frame,
    width=40
)

search_entry.pack(
    side="left",
    padx=5
)
search_entry.bind(
    "<Return>",
    search_results
)
status_label = tk.Label(
    root,
    text="Ready",
    fg="blue"
)

status_label.pack(pady=5)
progress = ttk.Progressbar(
    root,
    orient="horizontal",
    length=500,
    mode="indeterminate"
)

progress.pack(pady=5)
table_frame = tk.Frame(root)
table_frame.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)
tree = ttk.Treeview(
    table_frame,
    columns=("IP", "Hostname", "Ping", "Status"),
    show="headings"
)

tree.heading(
    "IP",
    text="IP",
    command=lambda: sort_column("IP", False)
)

tree.heading(
    "Hostname",
    text="Hostname",
    command=lambda: sort_column("Hostname", False)
)

tree.heading(
    "Ping",
    text="Ping",
    command=lambda: sort_column("Ping", False)
)

tree.heading(
    "Status",
    text="Status",
    command=lambda: sort_column("Status", False)
)
tree.column("IP", width=140)
tree.column("Hostname", width=350)
tree.column("Ping", width=80)
tree.column("Status", width=100)

tree.pack(
    side="left",
    fill="both",
    expand=True
)

scrollbar = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=tree.yview
)

scrollbar.pack(
    side="right",
    fill="y"
)

tree.configure(
    yscrollcommand=scrollbar.set
)
tree.tag_configure(
    "online",
    foreground="darkgreen",
    background="#e8ffe8"
)

tree.tag_configure(
    "offline",
    foreground="red",
    background="#ffe8e8"
)

root.mainloop()
