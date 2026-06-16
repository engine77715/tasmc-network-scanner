import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import socket
import subprocess
import os
from scanner import scan_network
from exporter import export_to_excel

# ── темы ──────────────────────────────────────────────────────────────────────
THEMES = {
    "Light": {
        "bg":           "#f5f5f5",
        "fg":           "#000000",
        "btn_bg":       "#e0e0e0",
        "btn_fg":       "#000000",
        "entry_bg":     "#ffffff",
        "entry_fg":     "#000000",
        "tree_bg":      "#ffffff",
        "tree_fg":      "#000000",
        "heading_bg":   "#d0d0d0",
        "online_bg":    "#e8ffe8",
        "online_fg":    "darkgreen",
        "offline_bg":   "#ffe8e8",
        "offline_fg":   "red",
        "status_fg":    "blue",
        "statusbar_bg": "#e0e0e0",
        "statusbar_fg": "#333333",
        "select_bg":    "#0078d7",
        "select_fg":    "#ffffff",
        "progress_bg":  "#0078d7",
        "progress_tr":  "#cccccc",
    },
    "Dark": {
        "bg":           "#1e1e1e",
        "fg":           "#dcdcdc",
        "btn_bg":       "#3c3c3c",
        "btn_fg":       "#ffffff",
        "entry_bg":     "#2d2d2d",
        "entry_fg":     "#dcdcdc",
        "tree_bg":      "#252526",
        "tree_fg":      "#dcdcdc",
        "heading_bg":   "#3c3c3c",
        "online_bg":    "#1a3a1a",
        "online_fg":    "#4ec94e",
        "offline_bg":   "#3a1a1a",
        "offline_fg":   "#ff6b6b",
        "status_fg":    "#4fc3f7",
        "statusbar_bg": "#007acc",
        "statusbar_fg": "#ffffff",
        "select_bg":    "#264f78",
        "select_fg":    "#ffffff",
        "progress_bg":  "#4fc3f7",
        "progress_tr":  "#3c3c3c",
    }
}

current_theme = "Light"
results       = []
_scan_total   = 254
_scan_done    = 0
_scan_lock    = threading.Lock()

vlans = {
    "150": "10.101.150.",
    "110": "10.101.110.",
    "118": "10.101.118.",
    "113": "10.101.113."
}

def get_my_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "N/A"

MY_IP = get_my_ip()

# ══════════════════════════════════════════════════════════════════════════════
root = tk.Tk()
root.title("TASMC Network Scanner")
root.geometry("1100x700")

_style = ttk.Style()
_style.theme_use("clam")
_style.configure("TProgressbar",
                 background="#0078d7",
                 troughcolor="#cccccc",
                 thickness=18)
# ══════════════════════════════════════════════════════════════════════════════

def apply_theme(theme_name):
    global current_theme
    current_theme = theme_name
    t = THEMES[theme_name]
    root.configure(bg=t["bg"])

    for widget in all_widgets:
        cls = widget.winfo_class()
        try:
            if cls == "Frame":
                widget.configure(bg=t["bg"])
            elif cls == "Label":
                widget.configure(bg=t["bg"], fg=t["fg"])
            elif cls == "Button":
                widget.configure(bg=t["btn_bg"], fg=t["btn_fg"],
                                 activebackground=t["select_bg"],
                                 activeforeground=t["select_fg"])
            elif cls == "Entry":
                widget.configure(bg=t["entry_bg"], fg=t["entry_fg"],
                                 insertbackground=t["fg"])
            elif cls == "Radiobutton":
                widget.configure(bg=t["bg"], fg=t["fg"],
                                 activebackground=t["bg"],
                                 selectcolor=t["btn_bg"])
        except tk.TclError:
            pass

    status_label.configure(fg=t["status_fg"])
    title_label.configure(bg=t["bg"], fg=t["fg"])
    progress_pct_label.configure(bg=t["bg"], fg=t["fg"])

    statusbar_frame.configure(bg=t["statusbar_bg"])
    for lbl in [sb_left, sb_center, sb_right, sb_sep1, sb_sep2]:
        lbl.configure(bg=t["statusbar_bg"], fg=t["statusbar_fg"])

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview",
                    background=t["tree_bg"],
                    foreground=t["tree_fg"],
                    fieldbackground=t["tree_bg"],
                    rowheight=24)
    style.configure("Treeview.Heading",
                    background=t["heading_bg"],
                    foreground=t["fg"],
                    font=("Segoe UI", 10, "bold"))
    style.map("Treeview",
              background=[("selected", t["select_bg"])],
              foreground=[("selected", t["select_fg"])])
    style.configure("TCombobox",
                    fieldbackground=t["entry_bg"],
                    background=t["btn_bg"],
                    foreground=t["fg"])
    style.configure("TProgressbar",
                    background=t["progress_bg"],
                    troughcolor=t["progress_tr"],
                    thickness=18)
    style.configure("TScrollbar", background=t["btn_bg"])

    tree.tag_configure("online",  foreground=t["online_fg"],  background=t["online_bg"])
    tree.tag_configure("offline", foreground=t["offline_fg"], background=t["offline_bg"])
    theme_btn.configure(text="☀️ Light Mode" if theme_name == "Dark" else "🌙 Dark Mode")

def toggle_theme():
    apply_theme("Dark" if current_theme == "Light" else "Light")

# ── прогрессбар ───────────────────────────────────────────────────────────────
def reset_progress():
    progress["value"] = 0
    progress_pct_label.configure(text="")

def set_progress(done, total):
    pct = int(done / total * 100)
    progress["value"] = pct
    progress_pct_label.configure(text=f"{done} / {total}  ({pct}%)")

# ── сортировка ────────────────────────────────────────────────────────────────
def sort_column(col, reverse):
    data = [(tree.set(item, col), item) for item in tree.get_children("")]
    data.sort(reverse=reverse)
    for index, (_, item) in enumerate(data):
        tree.move(item, "", index)
    tree.heading(col, command=lambda: sort_column(col, not reverse))

# ── поиск ─────────────────────────────────────────────────────────────────────
def search_results(event=None):
    search_text = search_entry.get().lower()
    for item in tree.get_children():
        values = tree.item(item)["values"]
        if (search_text in str(values[0]).lower() or
                search_text in str(values[1]).lower() or
                search_text in str(values[4]).lower()):
            tree.selection_set(item)
            tree.focus(item)
            tree.see(item)
            break

# ── действия в окне хоста ─────────────────────────────────────────────────────
def action_rdp(ip):
    os.system(f"mstsc /v:{ip}")

def action_psexec(ip):
    os.system(f'start cmd /k "psexec \\\\{ip} -s cmd.exe"')

def action_netuse(ip, hostname):
    os.system(f'start cmd /k "net use \\\\{hostname} && echo. && echo Connected to {hostname} && cmd"')

def action_unc(hostname):
    os.startfile(f"\\\\{hostname}\\c$")

# ── info окно ─────────────────────────────────────────────────────────────────
def show_host_info(event):
    selected = tree.focus()
    if not selected:
        return
    values = tree.item(selected)["values"]
    ip, hostname, ping, status, mac = values
    t = THEMES[current_theme]

    win = tk.Toplevel(root)
    win.title(f"Host — {hostname}")
    win.geometry("500x420")
    win.resizable(False, False)
    win.configure(bg=t["bg"])

    # ── основная инфо ─────────────────────────────────────────────────────────
    for label, value in [("IP", ip), ("Hostname", hostname),
                         ("Ping", ping), ("Status", status), ("MAC", mac)]:
        row = tk.Frame(win, bg=t["bg"])
        row.pack(fill="x", padx=20, pady=3)
        tk.Label(row, text=f"{label}:", font=("Segoe UI", 10, "bold"),
                 width=10, anchor="w", bg=t["bg"], fg=t["fg"]).pack(side="left")
        tk.Label(row, text=str(value), font=("Segoe UI", 10),
                 anchor="w", bg=t["bg"], fg=t["fg"]).pack(side="left")

    # ── разделитель ───────────────────────────────────────────────────────────
    tk.Frame(win, height=1, bg=t["heading_bg"]).pack(fill="x", padx=20, pady=8)

    # ── logged-in user ────────────────────────────────────────────────────────
    tk.Label(win, text="👤 Logged-in User",
             font=("Segoe UI", 10, "bold"),
             bg=t["bg"], fg=t["fg"]).pack(anchor="w", padx=20)

    user_label = tk.Label(win, text="Checking...",
                          font=("Segoe UI", 10),
                          bg=t["bg"], fg=t["status_fg"])
    user_label.pack(anchor="w", padx=20, pady=4)

    # ── разделитель 2 ─────────────────────────────────────────────────────────
    tk.Frame(win, height=1, bg=t["heading_bg"]).pack(fill="x", padx=20, pady=6)

    # ── кнопки подключения ────────────────────────────────────────────────────
    tk.Label(win, text="🔌 Connect",
             font=("Segoe UI", 10, "bold"),
             bg=t["bg"], fg=t["fg"]).pack(anchor="w", padx=20)

    btn_frame = tk.Frame(win, bg=t["bg"])
    btn_frame.pack(pady=8, padx=20, fill="x")

    btn_cfg = {"bg": t["btn_bg"], "fg": t["btn_fg"], "width": 11,
               "font": ("Segoe UI", 9), "relief": "flat", "bd": 1}

    tk.Button(btn_frame, text="🖥️ RDP",
              **btn_cfg,
              command=lambda: action_rdp(ip)
              ).pack(side="left", padx=3)

    tk.Button(btn_frame, text="💻 PsExec",
              **btn_cfg,
              command=lambda: action_psexec(ip)
              ).pack(side="left", padx=3)

    tk.Button(btn_frame, text="🔗 Net Use",
              **btn_cfg,
              command=lambda: action_netuse(ip, hostname)
              ).pack(side="left", padx=3)

    tk.Button(btn_frame, text="📁 UNC",
              **btn_cfg,
              command=lambda: action_unc(hostname)
              ).pack(side="left", padx=3)

    tk.Button(btn_frame, text="🔄 Refresh",
              **btn_cfg,
              command=lambda: threading.Thread(
                  target=fetch_user,
                  args=(ip, user_label, t),
                  daemon=True).start()
              ).pack(side="left", padx=3)

    # ── запуск проверки юзера сразу ───────────────────────────────────────────
    threading.Thread(target=fetch_user,
                     args=(ip, user_label, t),
                     daemon=True).start()


def fetch_user(ip: str, label: tk.Label, t: dict):
    try:
        result = subprocess.run(
            ["query", "user", f"/server:{ip}"],
            capture_output=True,
            text=True,
            timeout=8
        )
        output = result.stdout.strip()

        if result.returncode != 0 or not output:
            # различаем access denied и просто пусто
            stderr = result.stderr.strip().lower()
            if "access" in stderr or "denied" in stderr:
                text  = "🔒 Access Denied"
            else:
                text  = "👻 No users logged in"
            color = t["offline_fg"]
        else:
            lines = [l for l in output.splitlines()
                     if l.strip() and not l.strip().upper().startswith("USERNAME")]
            if not lines:
                text  = "👻 No users logged in"
                color = t["offline_fg"]
            else:
                users = []
                for line in lines:
                    parts = line.split()
                    if parts:
                        username = parts[0].lstrip(">")
                        state    = parts[3] if len(parts) > 3 else "?"
                        logon    = " ".join(parts[5:]) if len(parts) > 5 else "?"
                        users.append(f"✅  {username}   [{state}]   logon: {logon}")
                text  = "\n".join(users)
                color = t["online_fg"]

    except subprocess.TimeoutExpired:
        text  = "⏱ Timeout — host unreachable"
        color = t["offline_fg"]
    except FileNotFoundError:
        text  = "❌ 'query' not found on this system"
        color = t["offline_fg"]
    except Exception as e:
        text  = f"Error: {e}"
        color = t["offline_fg"]

    label.after(0, lambda: label.configure(text=text, fg=color))

# ── контекстное меню ──────────────────────────────────────────────────────────
def show_context_menu(event):
    row = tree.identify_row(event.y)
    if not row:
        return
    tree.selection_set(row)
    tree.focus(row)
    context_menu.post(event.x_root, event.y_root)

def copy_ip():
    s = tree.focus()
    if s:
        root.clipboard_clear()
        root.clipboard_append(tree.item(s)["values"][0])

def copy_mac():
    s = tree.focus()
    if s:
        root.clipboard_clear()
        root.clipboard_append(tree.item(s)["values"][4])

def copy_hostname():
    s = tree.focus()
    if s:
        root.clipboard_clear()
        root.clipboard_append(tree.item(s)["values"][1])

def rdp_connect():
    s = tree.focus()
    if s:
        os.system(f"mstsc /v:{tree.item(s)['values'][0]}")

# ── фильтр ────────────────────────────────────────────────────────────────────
filter_var = tk.StringVar(value="ALL")

def apply_filter(*args):
    f = filter_var.get()
    for item in tree.get_children():
        tree.delete(item)
    shown = 0
    for row in results:
        ip, host, ping, status, mac = row
        if f == "ONLINE"  and status != "ONLINE":  continue
        if f == "OFFLINE" and status != "OFFLINE": continue
        tag = "online" if status == "ONLINE" else "offline"
        tree.insert("", "end", values=(ip, host, ping, status, mac), tags=(tag,))
        shown += 1
    update_sb_center(f"Showing {shown} of {len(results)} hosts")

# ── статусбар ─────────────────────────────────────────────────────────────────
def update_sb_left(text):   sb_left.configure(text=text)
def update_sb_center(text): sb_center.configure(text=text)
def update_sb_right(text):  sb_right.configure(text=text)

# ── callback прогресса ────────────────────────────────────────────────────────
def on_host_done():
    global _scan_done
    with _scan_lock:
        _scan_done += 1
        done  = _scan_done
        total = _scan_total
    root.after(0, set_progress, done, total)
    root.after(0, lambda: status_label.configure(
        text=f"Scanning...  {done} / {total}"))

# ── сканирование ──────────────────────────────────────────────────────────────
def start_scan():
    threading.Thread(target=run_scan, daemon=True).start()

def run_scan():
    global results, _scan_done, _scan_total
    selected_vlan = vlan_combo.get()

    scan_button.config(state="disabled")
    export_button.config(state="disabled")

    if selected_vlan == "ALL":
        networks    = list(vlans.values())
        _scan_total = 254 * len(networks)
    else:
        networks    = [vlans[selected_vlan]]
        _scan_total = 254

    _scan_done = 0
    root.after(0, reset_progress)
    root.after(0, lambda: status_label.configure(text="Scanning..."))
    update_sb_left(f"🔄 Scanning VLAN {selected_vlan}...")
    update_sb_center("")
    update_sb_right(f"My IP: {MY_IP}")

    scan_start    = time.time()
    scan_time_str = time.strftime("%H:%M:%S")

    all_results = []
    for network in networks:
        all_results.extend(scan_network(network, progress_callback=on_host_done))
    results = all_results

    duration     = time.time() - scan_start
    duration_str = f"{duration:.1f}s"

    online_count  = sum(1 for r in results if r[3] == "ONLINE")
    offline_count = sum(1 for r in results if r[3] == "OFFLINE")

    root.after(0, lambda: online_label.configure(text=f"🟢 ONLINE: {online_count}"))
    root.after(0, lambda: offline_label.configure(text=f"🔴 OFFLINE: {offline_count}"))
    root.after(0, lambda: [tree.delete(i) for i in tree.get_children()])

    for ip, host, ping, status, mac in results:
        tag = "online" if status == "ONLINE" else "offline"
        root.after(0, lambda r=(ip, host, ping, status, mac), tg=tag:
                   tree.insert("", "end", values=r, tags=(tg,)))

    root.after(0, lambda: set_progress(_scan_total, _scan_total))
    root.after(0, lambda: status_label.configure(
        text=f"Scan completed. Found {len(results)} hosts"))
    root.after(0, lambda: scan_button.configure(state="normal"))
    root.after(0, lambda: export_button.configure(state="normal"))

    update_sb_left(f"✅ Last scan: {scan_time_str}   ⏱ Duration: {duration_str}")
    update_sb_center(f"Showing {len(results)} of {len(results)} hosts")
    update_sb_right(f"My IP: {MY_IP}")

# ── экспорт ───────────────────────────────────────────────────────────────────
def export_results():
    if not results:
        messagebox.showwarning("No data", "Run a scan first before exporting.")
        return
    try:
        path = export_to_excel(results, vlan=vlan_combo.get())
        messagebox.showinfo("Export", f"Saved to:\n{path}")
    except Exception as e:
        messagebox.showerror("Export Error", str(e))

# ══════════════════════════════════════════════════════════════════════════════
# UI ВИДЖЕТЫ
# ══════════════════════════════════════════════════════════════════════════════

top_frame = tk.Frame(root)
top_frame.pack(fill="x", padx=15, pady=10)

title_label = tk.Label(top_frame, text="TASMC Network Scanner",
                       font=("Segoe UI", 20, "bold"))
title_label.pack(side="left")

theme_btn = tk.Button(top_frame, text="🌙 Dark Mode",
                      width=14, command=toggle_theme)
theme_btn.pack(side="right")

ctrl_frame = tk.Frame(root)
ctrl_frame.pack(pady=5)

tk.Label(ctrl_frame, text="VLAN:").pack(side="left")

vlan_combo = ttk.Combobox(ctrl_frame,
                          values=list(vlans.keys()) + ["ALL"],
                          state="readonly", width=10)
vlan_combo.set("150")
vlan_combo.pack(side="left", padx=10)

scan_button = tk.Button(ctrl_frame, text="▶ Start Scan",
                        width=16, command=start_scan)
scan_button.pack(side="left", padx=5)

export_button = tk.Button(ctrl_frame, text="📊 Export Excel",
                          width=16, command=export_results, state="disabled")
export_button.pack(side="left", padx=5)

info_frame = tk.Frame(root)
info_frame.pack(pady=3)

online_label  = tk.Label(info_frame, text="🟢 ONLINE: 0",  font=("Segoe UI", 10))
offline_label = tk.Label(info_frame, text="🔴 OFFLINE: 0", font=("Segoe UI", 10))
online_label.pack(side="left", padx=15)
offline_label.pack(side="left", padx=15)

tk.Label(info_frame, text="|", font=("Segoe UI", 10)).pack(side="left", padx=10)
tk.Label(info_frame, text="Show:", font=("Segoe UI", 10)).pack(side="left", padx=5)

for text, val in [("All", "ALL"), ("Online only", "ONLINE"), ("Offline only", "OFFLINE")]:
    tk.Radiobutton(info_frame, text=text, variable=filter_var,
                   value=val, command=apply_filter,
                   font=("Segoe UI", 10)).pack(side="left", padx=4)

search_frame = tk.Frame(root)
search_frame.pack(pady=4)

tk.Label(search_frame, text="Search:").pack(side="left")
search_entry = tk.Entry(search_frame, width=40)
search_entry.pack(side="left", padx=5)
search_entry.bind("<Return>", search_results)

status_label = tk.Label(root, text="Ready", font=("Segoe UI", 9))
status_label.pack(pady=2)

progress_frame = tk.Frame(root)
progress_frame.pack(pady=4, padx=20, fill="x")

progress = ttk.Progressbar(progress_frame,
                           orient="horizontal",
                           mode="determinate",
                           maximum=100)
progress.pack(side="left", fill="x", expand=True)

progress_pct_label = tk.Label(progress_frame, text="",
                               font=("Segoe UI", 9), width=18, anchor="w")
progress_pct_label.pack(side="left", padx=8)

table_frame = tk.Frame(root)
table_frame.pack(fill="both", expand=True, padx=10, pady=8)

tree = ttk.Treeview(table_frame,
                    columns=("IP", "Hostname", "Ping", "Status", "MAC"),
                    show="headings")

for col, width in [("IP", 130), ("Hostname", 280),
                   ("Ping", 70), ("Status", 90), ("MAC", 150)]:
    tree.heading(col, text=col, command=lambda c=col: sort_column(c, False))
    tree.column(col, width=width)

tree.pack(side="left", fill="both", expand=True)
tree.bind("<Double-1>", show_host_info)
tree.bind("<Button-3>", show_context_menu)

scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
scrollbar.pack(side="right", fill="y")
tree.configure(yscrollcommand=scrollbar.set)

context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="📋 Copy IP",       command=copy_ip)
context_menu.add_command(label="📋 Copy MAC",      command=copy_mac)
context_menu.add_command(label="📋 Copy Hostname", command=copy_hostname)
context_menu.add_separator()
context_menu.add_command(label="🖥️ RDP Connect",   command=rdp_connect)

statusbar_frame = tk.Frame(root, height=24)
statusbar_frame.pack(side="bottom", fill="x")

sb_left = tk.Label(statusbar_frame, text="Ready",
                   font=("Segoe UI", 9), anchor="w", padx=10)
sb_left.pack(side="left")

sb_sep1 = tk.Label(statusbar_frame, text="│", font=("Segoe UI", 9))
sb_sep1.pack(side="left")

sb_center = tk.Label(statusbar_frame, text="",
                     font=("Segoe UI", 9), anchor="center")
sb_center.pack(side="left", padx=20)

sb_sep2 = tk.Label(statusbar_frame, text="│", font=("Segoe UI", 9))
sb_sep2.pack(side="left")

sb_right = tk.Label(statusbar_frame, text=f"My IP: {MY_IP}",
                    font=("Segoe UI", 9), anchor="e", padx=10)
sb_right.pack(side="right")

all_widgets = [
    top_frame, ctrl_frame, info_frame, search_frame,
    table_frame, progress_frame,
    title_label, theme_btn, scan_button, export_button,
    online_label, offline_label, search_entry,
    status_label, progress_pct_label,
    *info_frame.winfo_children(),
    *search_frame.winfo_children(),
    *ctrl_frame.winfo_children(),
]

apply_theme("Light")
root.mainloop()