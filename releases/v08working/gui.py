import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import socket
import subprocess
import os
import re
from scanner import scan_network
from exporter import export_to_excel

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
        "toolbar_bg":   "#dcdcdc",
        "toolbar_sep":  "#aaaaaa",
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
        "toolbar_bg":   "#2d2d2d",
        "toolbar_sep":  "#555555",
    }
}

current_theme = "Light"
results       = []
_scan_total   = 254
_scan_done    = 0
_scan_lock    = threading.Lock()
_stop_flag    = threading.Event()

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
root.geometry("1150x720")

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

    toolbar.configure(bg=t["toolbar_bg"])
    for w in toolbar.winfo_children():
        cls = w.winfo_class()
        try:
            if cls == "Button":
                w.configure(bg=t["toolbar_bg"], fg=t["fg"],
                            activebackground=t["select_bg"],
                            activeforeground=t["select_fg"])
            elif cls == "Label":
                w.configure(bg=t["toolbar_bg"], fg=t["fg"])
            elif cls == "Frame":
                w.configure(bg=t["toolbar_sep"])
            elif cls == "Entry":
                w.configure(bg=t["entry_bg"], fg=t["entry_fg"],
                            insertbackground=t["fg"])
        except tk.TclError:
            pass

    ping_result_label.configure(bg=t["toolbar_bg"])

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
    tb_theme_btn.configure(text="☀️" if theme_name == "Dark" else "🌙")

def toggle_theme():
    apply_theme("Dark" if current_theme == "Light" else "Light")

def reset_progress():
    progress["value"] = 0
    progress_pct_label.configure(text="")

def set_progress(done, total):
    pct = int(done / total * 100)
    progress["value"] = pct
    progress_pct_label.configure(text=f"{done} / {total}  ({pct}%)")

def sort_column(col, reverse):
    data = [(tree.set(item, col), item) for item in tree.get_children("")]
    data.sort(reverse=reverse)
    for index, (_, item) in enumerate(data):
        tree.move(item, "", index)
    tree.heading(col, command=lambda: sort_column(col, not reverse))

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

def stop_scan():
    _stop_flag.set()
    tb_stop_btn.configure(state="disabled")
    status_label.configure(text="⏹ Scan stopped by user")

def copy_online_ips():
    online = [r[0] for r in results if r[3] == "ONLINE"]
    if not online:
        messagebox.showwarning("No data", "No online hosts found.")
        return
    root.clipboard_clear()
    root.clipboard_append("\n".join(online))
    messagebox.showinfo("Copied", f"{len(online)} online IPs copied!")

def ping_single(event=None):
    ip = ping_entry.get().strip()
    if not ip:
        return
    os.system(f'start cmd /k "ping -t {ip}"')

def action_rdp(ip):
    os.system(f"mstsc /v:{ip}")

def action_psexec(ip):
    os.system(f'start cmd /k "psexec \\\\{ip} -s cmd.exe"')

def action_netuse(ip, hostname):
    os.system(f'start cmd /k "net use \\\\{hostname} && echo. && echo Connected to {hostname} && cmd"')

def action_unc(hostname):
    # пробуем os.startfile, при ошибке — explorer как fallback
    try:
        os.startfile(f"\\\\{hostname}\\c$")
    except Exception:
        try:
            subprocess.Popen(["explorer", f"\\\\{hostname}\\c$"])
        except Exception as e:
            messagebox.showerror(
                "UNC Error",
                f"Cannot open  \\\\{hostname}\\c$\n\n"
                f"Possible reasons:\n"
                f"  • Host is offline or unreachable\n"
                f"  • File sharing is disabled\n"
                f"  • Firewall blocking SMB (port 445)\n\n"
                f"Try Net Use first to authenticate.\n\n"
                f"Details: {e}")

def action_compmgmt(hostname):
    os.system(f'mmc compmgmt.msc /computer:{hostname}')

def action_services(hostname):
    os.system(f'mmc services.msc /computer:{hostname}')

def action_eventlog(hostname):
    os.system(f'eventvwr.exe \\\\{hostname}')

# ── unjoin domain ─────────────────────────────────────────────────────────────
def action_unjoin_domain(hostname, win_parent):
    t = THEMES[current_theme]

    cred_win = tk.Toplevel(win_parent)
    cred_win.title(f"Unjoin Domain — {hostname}")
    cred_win.geometry("420x320")
    cred_win.resizable(False, False)
    cred_win.configure(bg=t["bg"])
    cred_win.grab_set()

    hdr = tk.Frame(cred_win, bg="#3a1a1a", pady=10)
    hdr.pack(fill="x")
    tk.Label(hdr, text="🔓  Remove PC from Domain",
             font=("Segoe UI", 11, "bold"),
             bg="#3a1a1a", fg="#ff6b6b").pack()
    tk.Label(hdr, text=f"Target: {hostname}",
             font=("Segoe UI", 9),
             bg="#3a1a1a", fg="#dcdcdc").pack()

    form = tk.Frame(cred_win, bg=t["bg"])
    form.pack(pady=15, padx=20, fill="x")

    def field(label_text, default="", show=None):
        row = tk.Frame(form, bg=t["bg"])
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label_text, width=12, anchor="w",
                 font=("Segoe UI", 9), bg=t["bg"], fg=t["fg"]).pack(side="left")
        kw = {"width": 28, "font": ("Segoe UI", 9),
              "bg": t["entry_bg"], "fg": t["entry_fg"],
              "insertbackground": t["fg"]}
        if show:
            kw["show"] = show
        e = tk.Entry(row, **kw)
        e.pack(side="left")
        e.insert(0, default)
        return e

    user_entry = field("Username:",  "TASMC\\")
    pass_entry = field("Password:",  show="*")
    wg_entry   = field("Workgroup:", "WORKGROUP")

    result_label = tk.Label(cred_win, text="",
                            font=("Segoe UI", 9),
                            bg=t["bg"], fg=t["offline_fg"],
                            wraplength=380, justify="center")
    result_label.pack(pady=4)

    def do_unjoin():
        username  = user_entry.get().strip()
        password  = pass_entry.get().strip()
        workgroup = wg_entry.get().strip() or "WORKGROUP"

        if not username or not password:
            result_label.configure(text="❌ Username and password required",
                                   fg=t["offline_fg"])
            return

        if not messagebox.askyesno(
                "Confirm Unjoin",
                f"Remove  {hostname}  from domain\n"
                f"and join workgroup  '{workgroup}'?\n\n"
                f"⚠️  The PC will reboot automatically!",
                parent=cred_win):
            return

        btn_ok.configure(state="disabled", text="⏳ Working...")
        result_label.configure(text="Executing PowerShell...",
                                fg=t["status_fg"])
        cred_win.update()

        threading.Thread(
            target=_do_unjoin_thread,
            args=(hostname, username, password, workgroup,
                  result_label, btn_ok, cred_win),
            daemon=True
        ).start()

    btn_row = tk.Frame(cred_win, bg=t["bg"])
    btn_row.pack(pady=6)

    btn_ok = tk.Button(btn_row, text="🔓 Remove from Domain",
                       bg="#cc4400", fg="#ffffff",
                       font=("Segoe UI", 10, "bold"),
                       relief="flat", cursor="hand2",
                       activebackground="#ff5500",
                       activeforeground="#ffffff",
                       command=do_unjoin)
    btn_ok.pack(side="left", padx=8)

    tk.Button(btn_row, text="Cancel",
              bg=t["btn_bg"], fg=t["btn_fg"],
              font=("Segoe UI", 9), relief="flat",
              command=cred_win.destroy).pack(side="left", padx=8)

    pass_entry.bind("<Return>", lambda e: do_unjoin())


def _do_unjoin_thread(hostname, username, password,
                      workgroup, result_label, btn_ok, cred_win):
    try:
        ps_script = (
            f"$pw = ConvertTo-SecureString '{password}' -AsPlainText -Force; "
            f"$cred = New-Object System.Management.Automation.PSCredential('{username}', $pw); "
            f"Remove-Computer -ComputerName '{hostname}' "
            f"-WorkgroupName '{workgroup}' -Credential $cred -Force -PassThru; "
            f"Start-Sleep -Seconds 2; "
            f"Restart-Computer -ComputerName '{hostname}' -Force"
        )

        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-Command", ps_script],
            capture_output=True, text=True, timeout=45
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode == 0 or "HasSucceeded" in stdout:
            text  = f"✅ Success!\n{hostname} removed from domain.\nRebooting in 2 seconds..."
            color = "darkgreen"
            result_label.after(4000, cred_win.destroy)
        else:
            err   = stderr or stdout or "Unknown error"
            err   = err.split("\n")[0][:150]
            text  = f"❌ Failed:\n{err}"
            color = "#ff6b6b"
            btn_ok.after(0, lambda: btn_ok.configure(
                state="normal", text="🔓 Remove from Domain"))

    except subprocess.TimeoutExpired:
        text  = "⏱ Timeout — PowerShell took too long"
        color = "#ff6b6b"
        btn_ok.after(0, lambda: btn_ok.configure(
            state="normal", text="🔓 Remove from Domain"))
    except Exception as e:
        err   = str(e)
        text  = f"❌ Error: {err}"
        color = "#ff6b6b"
        btn_ok.after(0, lambda: btn_ok.configure(
            state="normal", text="🔓 Remove from Domain"))

    result_label.after(0, lambda: result_label.configure(text=text, fg=color))

# ── fetch: logged-in user ─────────────────────────────────────────────────────
def fetch_user(ip, label, t):
    try:
        result = subprocess.run(
            ["query", "user", f"/server:{ip}"],
            capture_output=True, text=True, timeout=8)
        output = result.stdout.strip()
        if result.returncode != 0 or not output:
            stderr = result.stderr.strip().lower()
            text  = "🔒 Access Denied" if ("access" in stderr or "denied" in stderr) \
                    else "👻 No users logged in"
            color = t["offline_fg"]
        else:
            lines = [l for l in output.splitlines()
                     if l.strip() and not l.strip().upper().startswith("USERNAME")]
            if not lines:
                text, color = "👻 No users logged in", t["offline_fg"]
            else:
                users = []
                for line in lines:
                    parts    = line.split()
                    username = parts[0].lstrip(">") if parts else "?"
                    state    = parts[3] if len(parts) > 3 else "?"
                    logon    = " ".join(parts[5:]) if len(parts) > 5 else "?"
                    users.append(f"✅  {username}   [{state}]   logon: {logon}")
                text, color = "\n".join(users), t["online_fg"]
    except subprocess.TimeoutExpired:
        text, color = "⏱ Timeout", t["offline_fg"]
    except FileNotFoundError:
        text, color = "❌ 'query' not found", t["offline_fg"]
    except Exception as e:
        text, color = f"Error: {e}", t["offline_fg"]
    label.after(0, lambda: label.configure(text=text, fg=color))

# ── fetch: printers ───────────────────────────────────────────────────────────
def fetch_printers(ip, tree_widget, status_lbl, t):
    try:
        result = subprocess.run(
            ["wmic", f"/node:{ip}", "printer", "get",
             "Name,PortName,Default,WorkOffline"],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace")

        lines = [l.rstrip() for l in result.stdout.splitlines()]
        lines = [l.lstrip('\ufeff') for l in lines if l.strip()]

        header = None
        header_idx = 0
        for i, line in enumerate(lines):
            if "Default" in line and "PortName" in line:
                header = line
                header_idx = i
                break

        if not header:
            err_txt = "❌ No printers or access denied"
            status_lbl.after(0, lambda: status_lbl.configure(
                text=err_txt, fg=t["offline_fg"]))
            return

        col_default  = header.index("Default")
        col_portname = header.index("PortName")
        col_workoff  = header.index("WorkOffline")
        tmp          = header.replace("PortName", "--------")
        col_name     = tmp.index("Name")
        data         = lines[header_idx+1:]

        def update():
            for row in tree_widget.get_children():
                tree_widget.delete(row)
            for line in data:
                if not line.strip():
                    continue
                try:
                    default     = line[col_default:col_name].strip()
                    default     = "✅" if default.upper() == "TRUE" else ""
                    name        = line[col_name:col_portname].strip()
                    port        = line[col_portname:col_workoff].strip()
                    offline_val = line[col_workoff:].strip()
                    status_v    = "Offline" if offline_val.upper() == "TRUE" else "Online"
                    if name:
                        tree_widget.insert("", "end",
                                           values=(name, port, default, status_v))
                except Exception:
                    continue
            count = len(tree_widget.get_children())
            if count == 0:
                status_lbl.configure(text="👻 No printers found", fg=t["offline_fg"])
            else:
                status_lbl.configure(text=f"🖨️ Found {count} printer(s)", fg=t["online_fg"])

        status_lbl.after(0, update)

    except subprocess.TimeoutExpired:
        status_lbl.after(0, lambda: status_lbl.configure(
            text="⏱ Timeout", fg=t["offline_fg"]))
    except Exception as e:
        err = str(e)
        status_lbl.after(0, lambda: status_lbl.configure(
            text=f"Error: {err}", fg=t["offline_fg"]))

# ── fetch: system info ────────────────────────────────────────────────────────
def fetch_system_info(ip, text_widget, status_lbl, t):
    def run_wmic(args, skip_headers):
        try:
            r = subprocess.run(["wmic", f"/node:{ip}"] + args,
                               capture_output=True, text=True, timeout=12,
                               encoding="utf-8", errors="replace")
            lines = [l.strip().lstrip('\ufeff') for l in r.stdout.splitlines()
                     if l.strip() and not any(
                         l.strip().lstrip('\ufeff').startswith(h) for h in skip_headers)]
            return lines[0] if lines else "N/A"
        except Exception:
            return "N/A"

    os_info   = run_wmic(["os", "get", "Caption,Version"], ["Caption", "Version"])
    boot_time = run_wmic(["os", "get", "LastBootUpTime"],  ["LastBootUpTime"])
    computer  = run_wmic(["computersystem", "get", "Model,Manufacturer"],
                         ["Model", "Manufacturer"])
    serial    = run_wmic(["bios", "get", "SerialNumber"],  ["SerialNumber"])

    disks_fmt = []
    try:
        r = subprocess.run(
            ["wmic", f"/node:{ip}", "logicaldisk",
             "get", "DeviceID,Size,FreeSpace"],
            capture_output=True, text=True, timeout=12,
            encoding="utf-8", errors="replace")
        for l in r.stdout.splitlines():
            l = l.strip().lstrip('\ufeff')
            if not l or l.startswith("DeviceID"):
                continue
            parts = l.split()
            if len(parts) >= 3:
                try:
                    free  = int(parts[0]) // (1024**3)
                    did   = parts[1]
                    total = int(parts[2]) // (1024**3)
                    pct   = int((total - free) / total * 100) if total > 0 else 0
                    bar   = "█" * (pct // 10) + "░" * (10 - pct // 10)
                    disks_fmt.append(
                        f"  {did}  [{bar}] {pct}%  {free} GB free / {total} GB")
                except Exception:
                    disks_fmt.append(f"  {l}")
    except Exception:
        disks_fmt = ["  N/A"]

    boot_str = boot_time
    if len(boot_time) >= 14 and boot_time[0].isdigit():
        try:
            boot_str = (f"{boot_time[6:8]}/{boot_time[4:6]}/{boot_time[:4]} "
                        f"{boot_time[8:10]}:{boot_time[10:12]}")
        except Exception:
            boot_str = boot_time

    output = (f"{'─'*44}\n"
              f"  OS:        {os_info}\n"
              f"  Last Boot: {boot_str}\n"
              f"{'─'*44}\n"
              f"  Model:     {computer}\n"
              f"  Serial:    {serial}\n"
              f"{'─'*44}\n"
              f"  Disks:\n" + "\n".join(disks_fmt) + f"\n{'─'*44}")

    def update():
        text_widget.configure(state="normal")
        text_widget.delete("1.0", "end")
        text_widget.insert("end", output)
        text_widget.configure(state="disabled")
        status_lbl.configure(text="✅ Loaded", fg=t["online_fg"])

    status_lbl.after(0, update)

# ── fetch: services ───────────────────────────────────────────────────────────
def fetch_services(ip, tree_widget, status_lbl, t):
    try:
        result = subprocess.run(
            ["wmic", f"/node:{ip}", "service", "get",
             "DisplayName,Name,StartMode,State"],
            capture_output=True, text=True, timeout=25,
            encoding="utf-8", errors="replace")

        lines = [l.rstrip() for l in result.stdout.splitlines()]
        lines = [l.lstrip('\ufeff') for l in lines if l.strip()]

        header = None
        header_idx = 0
        for i, line in enumerate(lines):
            if "DisplayName" in line and "StartMode" in line:
                header = line
                header_idx = i
                break

        if not header:
            err_txt = "❌ No data or access denied"
            status_lbl.after(0, lambda: status_lbl.configure(
                text=err_txt, fg=t["offline_fg"]))
            return

        col_display   = header.index("DisplayName")
        col_name      = header.index("Name")
        col_startmode = header.index("StartMode")
        col_state     = header.index("State")
        data_lines    = [l for l in lines[header_idx+1:]
                         if l.strip() and len(l) > col_state]

        def update():
            for row in tree_widget.get_children():
                tree_widget.delete(row)
            if not data_lines:
                status_lbl.configure(text="❌ No services found", fg=t["offline_fg"])
                return
            running = 0
            for line in data_lines:
                try:
                    display   = line[col_display:col_name].strip()
                    name      = line[col_name:col_startmode].strip()
                    startmode = line[col_startmode:col_state].strip()
                    state     = line[col_state:].strip()
                    if not name:
                        continue
                    tag = "svc_run" if state.lower() == "running" else "svc_stop"
                    tree_widget.insert("", "end",
                                       values=(display, name, startmode, state),
                                       tags=(tag,))
                    if state.lower() == "running":
                        running += 1
                except Exception:
                    continue
            tree_widget.tag_configure("svc_run",  foreground=t["online_fg"])
            tree_widget.tag_configure("svc_stop", foreground=t["offline_fg"])
            total = len(tree_widget.get_children())
            status_lbl.configure(text=f"⚡ {running} running / {total} total",
                                  fg=t["online_fg"])

        status_lbl.after(0, update)

    except subprocess.TimeoutExpired:
        status_lbl.after(0, lambda: status_lbl.configure(
            text="⏱ Timeout", fg=t["offline_fg"]))
    except Exception as e:
        err = str(e)
        status_lbl.after(0, lambda: status_lbl.configure(
            text=f"Error: {err}", fg=t["offline_fg"]))

# ── fetch: installed software ─────────────────────────────────────────────────
def fetch_software(ip, tree_widget, status_lbl, t):
    try:
        result = subprocess.run(
            ["wmic", f"/node:{ip}", "product", "get", "Name,Version,Vendor"],
            capture_output=True, text=True, timeout=60,
            encoding="utf-8", errors="replace")

        lines = [l.rstrip() for l in result.stdout.splitlines()]
        lines = [l.lstrip('\ufeff') for l in lines if l.strip()]

        header = None
        header_idx = 0
        for i, line in enumerate(lines):
            if "Name" in line and "Version" in line and "Vendor" in line:
                header = line
                header_idx = i
                break

        if not header:
            err_txt = "❌ No data or access denied"
            status_lbl.after(0, lambda: status_lbl.configure(
                text=err_txt, fg=t["offline_fg"]))
            return

        tmp_h       = header.replace("Vendor", "------")
        col_name    = tmp_h.index("Name") if "Name" in tmp_h else 0
        col_vendor  = header.index("Vendor")  if "Vendor"  in header else None
        col_version = header.index("Version") if "Version" in header else None
        data        = lines[header_idx+1:]

        def update():
            for row in tree_widget.get_children():
                tree_widget.delete(row)
            for line in data:
                if not line.strip():
                    continue
                try:
                    name    = line[col_name:col_vendor].strip()    if col_vendor  else line[col_name:].strip()
                    vendor  = line[col_vendor:col_version].strip() if col_vendor and col_version else ""
                    version = line[col_version:].strip()            if col_version else ""
                    if name:
                        tree_widget.insert("", "end", values=(name, version, vendor))
                except Exception:
                    continue
            status_lbl.configure(
                text=f"📋 Found {len(tree_widget.get_children())} programs",
                fg=t["online_fg"])

        status_lbl.after(0, update)

    except subprocess.TimeoutExpired:
        status_lbl.after(0, lambda: status_lbl.configure(
            text="⏱ Timeout (wmic product slow — up to 60s)",
            fg=t["offline_fg"]))
    except Exception as e:
        err = str(e)
        status_lbl.after(0, lambda: status_lbl.configure(
            text=f"Error: {err}", fg=t["offline_fg"]))

# ── remote power ──────────────────────────────────────────────────────────────
def remote_reboot(hostname):
    if messagebox.askyesno("Confirm Reboot", f"Reboot {hostname} now?"):
        r = subprocess.run(
            ["shutdown", "/r", f"/m:\\\\{hostname}", "/t", "0"],
            capture_output=True, text=True)
        if r.returncode == 0:
            messagebox.showinfo("Reboot", f"✅ Reboot sent to {hostname}")
        else:
            messagebox.showerror("Error", r.stderr or "Failed")

def remote_shutdown(hostname):
    if messagebox.askyesno("Confirm Shutdown", f"Shutdown {hostname} now?"):
        r = subprocess.run(
            ["shutdown", "/s", f"/m:\\\\{hostname}", "/t", "0"],
            capture_output=True, text=True)
        if r.returncode == 0:
            messagebox.showinfo("Shutdown", f"✅ Shutdown sent to {hostname}")
        else:
            messagebox.showerror("Error", r.stderr or "Failed")

# ── info окно с вкладками ─────────────────────────────────────────────────────
def show_host_info(event):
    selected = tree.focus()
    if not selected:
        return
    values = tree.item(selected)["values"]
    ip, hostname, ping, status, mac = values
    t = THEMES[current_theme]

    win = tk.Toplevel(root)
    win.title(f"Host — {hostname}")
    win.geometry("620x580")
    win.resizable(False, False)
    win.configure(bg=t["bg"])

    notebook = ttk.Notebook(win)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # ── вкладка 1: Info ───────────────────────────────────────────────────────
    tab_info = tk.Frame(notebook, bg=t["bg"])
    notebook.add(tab_info, text="ℹ️ Info")

    for label, value in [("IP", ip), ("Hostname", hostname),
                         ("Ping", ping), ("Status", status), ("MAC", mac)]:
        row = tk.Frame(tab_info, bg=t["bg"])
        row.pack(fill="x", padx=20, pady=3)
        tk.Label(row, text=f"{label}:", font=("Segoe UI", 10, "bold"),
                 width=10, anchor="w", bg=t["bg"], fg=t["fg"]).pack(side="left")
        tk.Label(row, text=str(value), font=("Segoe UI", 10),
                 anchor="w", bg=t["bg"], fg=t["fg"]).pack(side="left")

    tk.Frame(tab_info, height=1, bg=t["heading_bg"]).pack(fill="x", padx=20, pady=6)
    tk.Label(tab_info, text="👤 Logged-in User",
             font=("Segoe UI", 10, "bold"), bg=t["bg"], fg=t["fg"]).pack(anchor="w", padx=20)

    user_label = tk.Label(tab_info, text="Checking...",
                          font=("Segoe UI", 10), bg=t["bg"], fg=t["status_fg"])
    user_label.pack(anchor="w", padx=20, pady=3)

    tk.Frame(tab_info, height=1, bg=t["heading_bg"]).pack(fill="x", padx=20, pady=6)
    tk.Label(tab_info, text="🔌 Connect",
             font=("Segoe UI", 10, "bold"), bg=t["bg"], fg=t["fg"]).pack(anchor="w", padx=20)

    btn_cfg  = {"bg": t["btn_bg"], "fg": t["btn_fg"], "width": 11,
                "font": ("Segoe UI", 9), "relief": "flat", "bd": 1}
    btn_cfg2 = {"bg": t["btn_bg"], "fg": t["btn_fg"], "width": 13,
                "font": ("Segoe UI", 9), "relief": "flat", "bd": 1}

    btn_frame = tk.Frame(tab_info, bg=t["bg"])
    btn_frame.pack(pady=4, padx=20, fill="x")

    tk.Button(btn_frame, text="🖥️ RDP",     **btn_cfg,
              command=lambda: action_rdp(ip)).pack(side="left", padx=3)
    tk.Button(btn_frame, text="💻 PsExec",  **btn_cfg,
              command=lambda: action_psexec(ip)).pack(side="left", padx=3)
    tk.Button(btn_frame, text="🔗 Net Use", **btn_cfg,
              command=lambda: action_netuse(ip, hostname)).pack(side="left", padx=3)
    tk.Button(btn_frame, text="📁 UNC",     **btn_cfg,
              command=lambda: action_unc(hostname)).pack(side="left", padx=3)
    tk.Button(btn_frame, text="🔄 Refresh", **btn_cfg,
              command=lambda: threading.Thread(
                  target=fetch_user, args=(ip, user_label, t),
                  daemon=True).start()).pack(side="left", padx=3)

    tk.Label(tab_info, text="🛠️ Management Tools",
             font=("Segoe UI", 10, "bold"), bg=t["bg"], fg=t["fg"]).pack(
        anchor="w", padx=20, pady=(6, 0))

    btn_frame2 = tk.Frame(tab_info, bg=t["bg"])
    btn_frame2.pack(pady=4, padx=20, fill="x")

    tk.Button(btn_frame2, text="🖥 Comp Mgmt",     **btn_cfg2,
              command=lambda: action_compmgmt(hostname)).pack(side="left", padx=3)
    tk.Button(btn_frame2, text="⚙️ Services",      **btn_cfg2,
              command=lambda: action_services(hostname)).pack(side="left", padx=3)
    tk.Button(btn_frame2, text="📋 Event Log",     **btn_cfg2,
              command=lambda: action_eventlog(hostname)).pack(side="left", padx=3)
    tk.Button(btn_frame2, text="🔓 Unjoin Domain",
              bg="#8b0000", fg="#ffffff", width=13,
              font=("Segoe UI", 9), relief="flat", bd=1,
              command=lambda: action_unjoin_domain(hostname, win)
              ).pack(side="left", padx=3)

    threading.Thread(target=fetch_user, args=(ip, user_label, t), daemon=True).start()

    # ── вкладка 2: Printers ───────────────────────────────────────────────────
    tab_printers = tk.Frame(notebook, bg=t["bg"])
    notebook.add(tab_printers, text="🖨️ Printers")

    pr_status = tk.Label(tab_printers, text="Loading...",
                         font=("Segoe UI", 9), bg=t["bg"], fg=t["status_fg"])
    pr_status.pack(anchor="w", padx=10, pady=4)

    pr_frame = tk.Frame(tab_printers, bg=t["bg"])
    pr_frame.pack(fill="both", expand=True, padx=10, pady=4)

    pr_tree = ttk.Treeview(pr_frame,
                           columns=("Name", "Port", "Default", "Status"),
                           show="headings", height=9)
    for col, w, anc in [("Name", 220, "w"), ("Port", 120, "w"),
                        ("Default", 60, "center"), ("Status", 80, "center")]:
        pr_tree.heading(col, text=col)
        pr_tree.column(col, width=w, anchor=anc)
    pr_tree.pack(side="left", fill="both", expand=True)
    ttk.Scrollbar(pr_frame, orient="vertical",
                  command=pr_tree.yview).pack(side="right", fill="y")

    pr_btn = tk.Frame(tab_printers, bg=t["bg"])
    pr_btn.pack(pady=6)
    tk.Button(pr_btn, text="🔄 Refresh", bg=t["btn_bg"], fg=t["btn_fg"],
              font=("Segoe UI", 9), relief="flat",
              command=lambda: threading.Thread(
                  target=fetch_printers, args=(ip, pr_tree, pr_status, t),
                  daemon=True).start()).pack(side="left", padx=5)
    tk.Button(pr_btn, text="🖨️ Open in CMD", bg=t["btn_bg"], fg=t["btn_fg"],
              font=("Segoe UI", 9), relief="flat",
              command=lambda: os.system(
                  f'start cmd /k "wmic /node:{ip} printer list brief & pause"')
              ).pack(side="left", padx=5)

    threading.Thread(target=fetch_printers,
                     args=(ip, pr_tree, pr_status, t), daemon=True).start()

    # ── вкладка 3: System ─────────────────────────────────────────────────────
    tab_system = tk.Frame(notebook, bg=t["bg"])
    notebook.add(tab_system, text="💻 System")

    sys_status = tk.Label(tab_system, text="Loading...",
                          font=("Segoe UI", 9), bg=t["bg"], fg=t["status_fg"])
    sys_status.pack(anchor="w", padx=10, pady=4)

    sys_text = tk.Text(tab_system, font=("Consolas", 9),
                       bg=t["entry_bg"], fg=t["fg"],
                       relief="flat", state="disabled", wrap="word", height=15)
    sys_text.pack(fill="both", expand=True, padx=10, pady=4)

    tk.Button(tab_system, text="🔄 Refresh", bg=t["btn_bg"], fg=t["btn_fg"],
              font=("Segoe UI", 9), relief="flat",
              command=lambda: threading.Thread(
                  target=fetch_system_info,
                  args=(ip, sys_text, sys_status, t),
                  daemon=True).start()).pack(pady=4)

    threading.Thread(target=fetch_system_info,
                     args=(ip, sys_text, sys_status, t), daemon=True).start()

    # ── вкладка 4: Services ───────────────────────────────────────────────────
    tab_services = tk.Frame(notebook, bg=t["bg"])
    notebook.add(tab_services, text="⚡ Services")

    svc_status = tk.Label(tab_services, text="Loading services...",
                          font=("Segoe UI", 9), bg=t["bg"], fg=t["status_fg"])
    svc_status.pack(anchor="w", padx=10, pady=4)

    svc_filter_var   = tk.StringVar(value="ALL")
    svc_filter_frame = tk.Frame(tab_services, bg=t["bg"])
    svc_filter_frame.pack(anchor="w", padx=10)
    svc_tree_ref     = [None]

    def filter_services():
        if not svc_tree_ref[0]:
            return
        f = svc_filter_var.get()
        for item in svc_tree_ref[0].get_children():
            vals  = svc_tree_ref[0].item(item)["values"]
            state = str(vals[3]).lower() if len(vals) > 3 else ""
            if f == "RUNNING" and state != "running":
                svc_tree_ref[0].detach(item)
            elif f == "STOPPED" and state == "running":
                svc_tree_ref[0].detach(item)
            else:
                try:
                    svc_tree_ref[0].reattach(item, "", "end")
                except Exception:
                    pass

    for txt, val in [("All", "ALL"), ("Running", "RUNNING"), ("Stopped", "STOPPED")]:
        tk.Radiobutton(svc_filter_frame, text=txt,
                       variable=svc_filter_var, value=val,
                       command=filter_services,
                       bg=t["bg"], fg=t["fg"],
                       font=("Segoe UI", 9)).pack(side="left", padx=4)

    svc_frame = tk.Frame(tab_services, bg=t["bg"])
    svc_frame.pack(fill="both", expand=True, padx=10, pady=4)

    svc_tree = ttk.Treeview(svc_frame,
                            columns=("Display", "Name", "Start", "State"),
                            show="headings", height=9)
    svc_tree_ref[0] = svc_tree
    for col, w, anc in [("Display", 220, "w"), ("Name", 150, "w"),
                        ("Start", 80, "center"), ("State", 80, "center")]:
        svc_tree.heading(col, text=col)
        svc_tree.column(col, width=w, anchor=anc)
    svc_tree.pack(side="left", fill="both", expand=True)
    ttk.Scrollbar(svc_frame, orient="vertical",
                  command=svc_tree.yview).pack(side="right", fill="y")

    tk.Button(tab_services, text="🔄 Refresh", bg=t["btn_bg"], fg=t["btn_fg"],
              font=("Segoe UI", 9), relief="flat",
              command=lambda: threading.Thread(
                  target=fetch_services, args=(ip, svc_tree, svc_status, t),
                  daemon=True).start()).pack(pady=4)

    threading.Thread(target=fetch_services,
                     args=(ip, svc_tree, svc_status, t), daemon=True).start()

    # ── вкладка 5: Software ───────────────────────────────────────────────────
    tab_software = tk.Frame(notebook, bg=t["bg"])
    notebook.add(tab_software, text="📋 Software")

    sw_status = tk.Label(tab_software,
                         text="⚠️ Click Load — may take up to 60 sec",
                         font=("Segoe UI", 9), bg=t["bg"], fg=t["status_fg"])
    sw_status.pack(anchor="w", padx=10, pady=4)

    sw_frame = tk.Frame(tab_software, bg=t["bg"])
    sw_frame.pack(fill="both", expand=True, padx=10, pady=4)

    sw_tree = ttk.Treeview(sw_frame,
                           columns=("Name", "Version", "Vendor"),
                           show="headings", height=9)
    for col, w, anc in [("Name", 250, "w"),
                        ("Version", 100, "center"), ("Vendor", 150, "w")]:
        sw_tree.heading(col, text=col)
        sw_tree.column(col, width=w, anchor=anc)
    sw_tree.pack(side="left", fill="both", expand=True)
    ttk.Scrollbar(sw_frame, orient="vertical",
                  command=sw_tree.yview).pack(side="right", fill="y")

    sw_btn = tk.Frame(tab_software, bg=t["bg"])
    sw_btn.pack(pady=4)
    tk.Button(sw_btn, text="📋 Load Software List",
              bg=t["btn_bg"], fg=t["btn_fg"],
              font=("Segoe UI", 9), relief="flat",
              command=lambda: threading.Thread(
                  target=fetch_software, args=(ip, sw_tree, sw_status, t),
                  daemon=True).start()).pack(side="left", padx=5)

    # ── вкладка 6: Power ──────────────────────────────────────────────────────
    tab_power = tk.Frame(notebook, bg=t["bg"])
    notebook.add(tab_power, text="🔋 Power")

    hdr_bg = "#3a1a1a"
    header_frame = tk.Frame(tab_power, bg=hdr_bg, pady=12)
    header_frame.pack(fill="x")

    tk.Label(header_frame, text="⚠️  Remote Power Management",
             font=("Segoe UI", 12, "bold"),
             bg=hdr_bg, fg="#ff6b6b").pack()
    tk.Label(header_frame, text=f"Target:  {hostname}",
             font=("Segoe UI", 10),
             bg=hdr_bg, fg="#dcdcdc").pack()

    tk.Frame(tab_power, height=1, bg=t["heading_bg"]).pack(fill="x")

    pw_frame = tk.Frame(tab_power, bg=t["bg"])
    pw_frame.pack(pady=25)

    reboot_frame = tk.Frame(pw_frame, bg=t["bg"])
    reboot_frame.pack(side="left", padx=20)
    tk.Button(reboot_frame, text="🔄  Reboot",
              bg="#cc4400", fg="#ffffff",
              font=("Segoe UI", 12, "bold"),
              width=14, height=2, relief="flat", cursor="hand2",
              activebackground="#ff5500", activeforeground="#ffffff",
              command=lambda: remote_reboot(hostname)).pack()
    tk.Label(reboot_frame, text="Restarts the computer",
             font=("Segoe UI", 8), bg=t["bg"], fg=t["fg"]).pack(pady=4)

    shutdown_frame = tk.Frame(pw_frame, bg=t["bg"])
    shutdown_frame.pack(side="left", padx=20)
    tk.Button(shutdown_frame, text="⏹  Shutdown",
              bg="#880000", fg="#ffffff",
              font=("Segoe UI", 12, "bold"),
              width=14, height=2, relief="flat", cursor="hand2",
              activebackground="#aa0000", activeforeground="#ffffff",
              command=lambda: remote_shutdown(hostname)).pack()
    tk.Label(shutdown_frame, text="Powers off the computer",
             font=("Segoe UI", 8), bg=t["bg"], fg=t["fg"]).pack(pady=4)

    tk.Frame(tab_power, height=1, bg=t["heading_bg"]).pack(fill="x", padx=20)

    info_pw = tk.Frame(tab_power, bg=t["bg"])
    info_pw.pack(pady=12, padx=20, fill="x")

    for icon, txt in [
        ("🔑", "Requires local admin rights on the remote host"),
        ("⚡", "Actions execute immediately with no delay"),
        ("💾", "Unsaved work on the remote PC will be lost"),
    ]:
        pw_row = tk.Frame(info_pw, bg=t["bg"])
        pw_row.pack(anchor="w", pady=2)
        tk.Label(pw_row, text=icon, font=("Segoe UI", 10),
                 bg=t["bg"]).pack(side="left", padx=(0, 6))
        tk.Label(pw_row, text=txt, font=("Segoe UI", 9),
                 bg=t["bg"], fg=t["fg"]).pack(side="left")

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

def update_sb_left(text):   sb_left.configure(text=text)
def update_sb_center(text): sb_center.configure(text=text)
def update_sb_right(text):  sb_right.configure(text=text)

def on_host_done():
    global _scan_done
    with _scan_lock:
        _scan_done += 1
        done  = _scan_done
        total = _scan_total
    root.after(0, set_progress, done, total)
    root.after(0, lambda: status_label.configure(
        text=f"Scanning...  {done} / {total}"))

def start_scan():
    threading.Thread(target=run_scan, daemon=True).start()

def run_scan():
    global results, _scan_done, _scan_total
    _stop_flag.clear()
    selected_vlan = vlan_combo.get()

    scan_button.configure(state="disabled")
    export_button.configure(state="disabled")
    root.after(0, lambda: tb_stop_btn.configure(state="normal"))
    root.after(0, lambda: tb_export_btn.configure(state="disabled"))
    root.after(0, lambda: tb_copy_btn.configure(state="disabled"))

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
        if _stop_flag.is_set():
            break
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
    msg = (f"⏹ Stopped. Found {len(results)} hosts so far"
           if _stop_flag.is_set()
           else f"Scan completed. Found {len(results)} hosts")
    root.after(0, lambda: status_label.configure(text=msg))
    root.after(0, lambda: scan_button.configure(state="normal"))
    root.after(0, lambda: export_button.configure(state="normal"))
    root.after(0, lambda: tb_stop_btn.configure(state="disabled"))
    root.after(0, lambda: tb_export_btn.configure(state="normal"))
    root.after(0, lambda: tb_copy_btn.configure(state="normal"))

    update_sb_left(f"✅ Last scan: {scan_time_str}   ⏱ Duration: {duration_str}")
    update_sb_center(f"Showing {len(results)} of {len(results)} hosts")
    update_sb_right(f"My IP: {MY_IP}")

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
top_frame.pack(fill="x", padx=15, pady=(10, 4))

title_label = tk.Label(top_frame, text="TASMC Network Scanner",
                       font=("Segoe UI", 20, "bold"))
title_label.pack(side="left")

theme_btn = tk.Button(top_frame, text="🌙 Dark Mode",
                      width=14, command=toggle_theme)
theme_btn.pack(side="right")

toolbar = tk.Frame(root, bd=1, relief="raised", height=36)
toolbar.pack(fill="x", padx=0, pady=0)

def tb_sep():
    tk.Frame(toolbar, width=1, bg="#aaaaaa").pack(
        side="left", fill="y", padx=5, pady=4)

TB = {"relief": "flat", "font": ("Segoe UI", 9), "bd": 0, "padx": 6, "pady": 3}

tb_scan_btn = tk.Button(toolbar, text="▶ Scan",      width=7,  **TB, command=start_scan)
tb_scan_btn.pack(side="left", padx=2, pady=2)
tb_stop_btn = tk.Button(toolbar, text="⏹ Stop",      width=7,  **TB,
                        state="disabled", command=stop_scan)
tb_stop_btn.pack(side="left", padx=2, pady=2)
tb_sep()
tb_export_btn = tk.Button(toolbar, text="📊 Export",  width=8,  **TB,
                          state="disabled", command=export_results)
tb_export_btn.pack(side="left", padx=2, pady=2)
tb_copy_btn = tk.Button(toolbar, text="📋 Copy IPs",  width=10, **TB,
                        state="disabled", command=copy_online_ips)
tb_copy_btn.pack(side="left", padx=2, pady=2)
tb_sep()
tk.Label(toolbar, text="🔍 Ping:", font=("Segoe UI", 9)).pack(
    side="left", padx=(4, 2), pady=2)
ping_entry = tk.Entry(toolbar, width=16, font=("Segoe UI", 9))
ping_entry.pack(side="left", pady=2)
ping_entry.bind("<Return>", ping_single)
tb_ping_btn = tk.Button(toolbar, text="Go", width=4, **TB, command=ping_single)
tb_ping_btn.pack(side="left", padx=2, pady=2)
ping_result_label = tk.Label(toolbar, text="", font=("Segoe UI", 9),
                              width=28, anchor="w")
ping_result_label.pack(side="left", padx=6)
tb_sep()
tb_theme_btn = tk.Button(toolbar, text="🌙", width=3, **TB, command=toggle_theme)
tb_theme_btn.pack(side="right", padx=4, pady=2)

ctrl_frame = tk.Frame(root)
ctrl_frame.pack(pady=5)
tk.Label(ctrl_frame, text="VLAN:").pack(side="left")
vlan_combo = ttk.Combobox(ctrl_frame, values=list(vlans.keys()) + ["ALL"],
                          state="readonly", width=10)
vlan_combo.set("150")
vlan_combo.pack(side="left", padx=10)
scan_button = tk.Button(ctrl_frame, text="▶ Start Scan", width=16, command=start_scan)
scan_button.pack(side="left", padx=5)
export_button = tk.Button(ctrl_frame, text="📊 Export Excel", width=16,
                          command=export_results, state="disabled")
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
progress = ttk.Progressbar(progress_frame, orient="horizontal",
                           mode="determinate", maximum=100)
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