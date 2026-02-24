import requests


class VPNApiClient:
    def __init__(self, base_url: str, verify_tls: bool = False):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.verify = verify_tls

    def login(self, username: str, password: str):
        response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"username": username, "password": password},
            timeout=15,
        )
        if response.status_code != 200:
            try:
                payload = response.json()
                message = payload.get("error", "Login failed")
            except Exception:
                message = "Login failed"
            raise RuntimeError(message)
        return response.json()

    def generate_config(self):
        response = self.session.post(
            f"{self.base_url}/api/config/generate",
            timeout=20,
        )
        if response.status_code != 200:
            try:
                payload = response.json()
                message = payload.get("error", "Config generation failed")
            except Exception:
                message = "Config generation failed"
            raise RuntimeError(message)

        payload = response.json()
        if "config" not in payload:
            raise RuntimeError("Server did not return a WireGuard config")
        return payload
