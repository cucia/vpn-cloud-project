import threading
import tkinter as tk
from tkinter import messagebox

import urllib3

from connector import connect_vpn, disconnect_vpn, ensure_privileges, get_status
from vpn_api import VPNApiClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class VPNDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VPN Cloud Desktop Client")
        self.root.geometry("520x420")

        self.api_client = None
        self.latest_config = None

        self.server_var = tk.StringVar(value="https://localhost")
        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")

        self._build_ui()

    def _build_ui(self):
        frame = tk.Frame(self.root, padx=16, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Server URL").pack(anchor="w")
        tk.Entry(frame, textvariable=self.server_var, width=60).pack(fill="x", pady=(0, 10))

        tk.Label(frame, text="Username").pack(anchor="w")
        tk.Entry(frame, textvariable=self.user_var, width=60).pack(fill="x", pady=(0, 10))

        tk.Label(frame, text="Password").pack(anchor="w")
        tk.Entry(frame, textvariable=self.pass_var, show="*", width=60).pack(fill="x", pady=(0, 14))

        btn_row = tk.Frame(frame)
        btn_row.pack(fill="x", pady=(0, 10))

        tk.Button(btn_row, text="Login + Connect", command=self.login_and_connect).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="Disconnect", command=self.disconnect).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="Refresh Status", command=self.refresh_status).pack(side="left")

        self.output = tk.Text(frame, height=12, wrap="word")
        self.output.pack(fill="both", expand=True, pady=(8, 0))

        status_bar = tk.Label(self.root, textvariable=self.status_var, anchor="w", relief="sunken")
        status_bar.pack(fill="x", side="bottom")

    def log(self, text):
        self.output.insert("end", text + "\n")
        self.output.see("end")

    def set_status(self, value):
        self.status_var.set(value)

    def _run_async(self, fn):
        thread = threading.Thread(target=fn, daemon=True)
        thread.start()

    def login_and_connect(self):
        def task():
            try:
                ensure_privileges()
                self.set_status("Connecting...")

                server = self.server_var.get().strip().rstrip('/')
                username = self.user_var.get().strip()
                password = self.pass_var.get().strip()

                if not server or not username or not password:
                    raise RuntimeError("Server URL, username, and password are required")

                self.api_client = VPNApiClient(server, verify_tls=False)
                self.log(f"Authenticating user {username}...")
                self.api_client.login(username, password)
                self.log("Login successful")

                payload = self.api_client.generate_config()
                self.latest_config = payload["config"]
                self.log(f"Config generated, assigned IP: {payload.get('assigned_ip', '-')}")

                result = connect_vpn(self.latest_config)
                self.log(result)
                self.set_status("Connected")
            except Exception as exc:
                self.set_status("Error")
                self.log(f"Error: {exc}")
                messagebox.showerror("Connection Failed", str(exc))

        self._run_async(task)

    def disconnect(self):
        def task():
            try:
                ensure_privileges()
                self.set_status("Disconnecting...")
                result = disconnect_vpn()
                self.log(result)
                self.set_status("Disconnected")
            except Exception as exc:
                self.set_status("Error")
                self.log(f"Error: {exc}")
                messagebox.showerror("Disconnect Failed", str(exc))

        self._run_async(task)

    def refresh_status(self):
        def task():
            try:
                status = get_status()
                self.log(f"Status: {status}")
                self.set_status("Status updated")
            except Exception as exc:
                self.set_status("Error")
                self.log(f"Error: {exc}")

        self._run_async(task)


if __name__ == "__main__":
    root = tk.Tk()
    app = VPNDesktopApp(root)
    root.mainloop()
