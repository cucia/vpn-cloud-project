import os
import platform
import subprocess
import tempfile
from pathlib import Path


WINDOWS_WIREGUARD_EXE = r"C:\Program Files\WireGuard\wireguard.exe"


def _run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def ensure_privileges():
    system = platform.system()
    if system == "Linux":
        if os.geteuid() != 0:
            raise RuntimeError("Run this app as root on Linux (e.g., sudo python app.py)")
    elif system == "Windows":
        try:
            import ctypes

            if not ctypes.windll.shell32.IsUserAnAdmin():
                raise RuntimeError("Run this app as Administrator on Windows")
        except Exception:
            raise RuntimeError("Run this app as Administrator on Windows")


def connect_vpn(config_text: str):
    system = platform.system()

    if system == "Linux":
        conf_path = Path("/etc/wireguard/wg0.conf")
        conf_path.parent.mkdir(parents=True, exist_ok=True)
        conf_path.write_text(config_text, encoding="utf-8")

        _run(["wg-quick", "down", "wg0"])
        code, _, err = _run(["wg-quick", "up", "wg0"])
        if code != 0:
            raise RuntimeError(err or "Failed to connect on Linux")
        return "Connected (Linux)"

    if system == "Windows":
        if not Path(WINDOWS_WIREGUARD_EXE).exists():
            raise RuntimeError("WireGuard is not installed. Install from https://www.wireguard.com/install/")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".conf", mode="w", encoding="utf-8") as fp:
            fp.write(config_text)
            temp_conf = fp.name

        _run([WINDOWS_WIREGUARD_EXE, "/uninstalltunnelservice", "wg0"])
        code, _, err = _run([WINDOWS_WIREGUARD_EXE, "/installtunnelservice", temp_conf])
        if code != 0:
            raise RuntimeError(err or "Failed to connect on Windows")
        return "Connected (Windows)"

    raise RuntimeError(f"Unsupported OS: {system}")


def disconnect_vpn():
    system = platform.system()

    if system == "Linux":
        code, _, err = _run(["wg-quick", "down", "wg0"])
        if code != 0:
            raise RuntimeError(err or "Failed to disconnect on Linux")
        return "Disconnected (Linux)"

    if system == "Windows":
        if not Path(WINDOWS_WIREGUARD_EXE).exists():
            raise RuntimeError("WireGuard is not installed")

        code, _, err = _run([WINDOWS_WIREGUARD_EXE, "/uninstalltunnelservice", "wg0"])
        if code != 0:
            raise RuntimeError(err or "Failed to disconnect on Windows")
        return "Disconnected (Windows)"

    raise RuntimeError(f"Unsupported OS: {system}")


def get_status():
    system = platform.system()

    if system == "Linux":
        code, out, _ = _run(["wg", "show", "wg0"])
        if code != 0:
            return "Not connected"
        return out or "Connected"

    if system == "Windows":
        code, out, err = _run(["sc", "query", "WireGuardTunnel$wg0"])
        output = f"{out}\n{err}".upper()
        if code == 0 and "RUNNING" in output:
            return "Connected"
        return "Not connected"

    return f"Unsupported OS: {system}"
