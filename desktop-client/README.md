# VPN Cloud Desktop Client (MVP)

Cross-platform desktop client for Linux and Windows.

## Features
- Login to VPN server API
- Generate WireGuard config
- Connect/disconnect tunnel from app
- View connection status

## Requirements
- Python 3.10+
- WireGuard client installed on OS
  - Linux: `wireguard-tools`
  - Windows: official WireGuard app (`wireguard.exe`)

## Run

### Linux
```bash
cd desktop-client
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
sudo python app.py
```

### Windows (PowerShell, Run as Administrator)
```powershell
cd desktop-client
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Default server URL is `https://localhost`.

## Packaging

### Windows EXE
```powershell
pip install pyinstaller
pyinstaller --onefile --noconsole app.py
```

### Linux binary
```bash
pip install pyinstaller
pyinstaller --onefile --noconsole app.py
```

Output binary will be in `dist/`.
