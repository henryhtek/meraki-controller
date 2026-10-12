"""
Meraki API Gateway – Flask app for Google Home, Amazon Alexa & IFTTT

Features:
- Enable / disable any Meraki switch port via simple authenticated endpoints
- Multi-port support (any valid port ID)
- Shared-secret authentication (query param or header)
- Status check endpoint
- Clean error handling and logging
- Environment-variable configuration

Example IFTTT webhook URLs:
  https://your-host/port/7/enable?token=YOUR_SECRET
  https://your-host/port/7/disable?token=YOUR_SECRET
"""

import os
import logging
from functools import wraps

from flask import Flask, request, jsonify
import requests

__version__ = "1.1.0"

# ---------------------------------------------------------------------------
# Configuration (prefer environment variables)
# ---------------------------------------------------------------------------
API_KEY = os.environ.get("MERAKI_API_KEY", "")
SERIAL = os.environ.get("SWITCH_SERIAL", "")          # e.g. "Q2XX-XXXX-XXXX"
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "")         # shared secret
BASE_URL = "https://api.meraki.com/api/v1"

# Optional: restrict which ports can be controlled (comma-separated)
# Leave empty to allow any port
ALLOWED_PORTS = {
    p.strip()
    for p in os.environ.get("ALLOWED_PORTS", "").split(",")
    if p.strip()
}

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("meraki-api-gateway")


def require_auth(f):
    """Simple shared-secret authentication decorator."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Accept token from query string OR header
        token = request.args.get("token") or request.headers.get("X-Auth-Token")
        if not AUTH_TOKEN:
            logger.warning("AUTH_TOKEN is not set – authentication disabled")
        elif token != AUTH_TOKEN:
            logger.warning("Unauthorized access attempt from %s", request.remote_addr)
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


def meraki_headers():
    return {
        "X-Cisco-Meraki-API-Key": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def update_port(port_id: str, enabled: bool) -> tuple[int, dict | str]:
    """Call Meraki API to enable or disable a port."""
    if not API_KEY or not SERIAL:
        return 500, {"error": "Server misconfigured: MERAKI_API_KEY or SWITCH_SERIAL missing"}

    if ALLOWED_PORTS and port_id not in ALLOWED_PORTS:
        return 403, {"error": f"Port {port_id} is not in the allowed list"}

    url = f"{BASE_URL}/devices/{SERIAL}/switch/ports/{port_id}"
    payload = {"enabled": enabled}

    try:
        resp = requests.put(url, headers=meraki_headers(), json=payload, timeout=15)
        if resp.status_code == 200:
            return 200, resp.json()
        # Meraki often returns useful error messages
        try:
            err = resp.json()
        except Exception:
            err = resp.text
        logger.error("Meraki API error %s: %s", resp.status_code, err)
        return resp.status_code, {"error": err}
    except requests.RequestException as exc:
        logger.exception("Network error talking to Meraki")
        return 502, {"error": str(exc)}


def get_port_status(port_id: str) -> tuple[int, dict | str]:
    """Retrieve current configuration of a single port."""
    if not API_KEY or not SERIAL:
        return 500, {"error": "Server misconfigured"}

    url = f"{BASE_URL}/devices/{SERIAL}/switch/ports/{port_id}"
    try:
        resp = requests.get(url, headers=meraki_headers(), timeout=15)
        if resp.status_code == 200:
            return 200, resp.json()
        try:
            err = resp.json()
        except Exception:
            err = resp.text
        return resp.status_code, {"error": err}
    except requests.RequestException as exc:
        return 502, {"error": str(exc)}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return jsonify({
        "service": "Meraki API Gateway",
        "version": __version__,
        "endpoints": {
            "enable":  "POST /port/<port_id>/enable?token=SECRET",
            "disable": "POST /port/<port_id>/disable?token=SECRET",
            "status":  "GET  /port/<port_id>/status?token=SECRET",
            "health":  "GET  /health",
        },
        "auth": "Pass token as query param ?token=... or header X-Auth-Token",
    })


@app.route("/health")
def health():
    """Simple health check (no auth required)."""
    ok = bool(API_KEY and SERIAL and AUTH_TOKEN)
    return jsonify({
        "status": "ok" if ok else "misconfigured",
        "version": __version__,
        "meraki_key_set": bool(API_KEY),
        "serial_set": bool(SERIAL),
        "auth_token_set": bool(AUTH_TOKEN),
        "allowed_ports": sorted(ALLOWED_PORTS) if ALLOWED_PORTS else "all",
    }), 200 if ok else 503


@app.route("/port/<port_id>/enable", methods=["POST", "GET"])
@require_auth
def enable_port(port_id: str):
    """Enable a switch port."""
    code, body = update_port(port_id, True)
    if code == 200:
        logger.info("Port %s ENABLED by %s", port_id, request.remote_addr)
        return jsonify({
            "status": "success",
            "action": "enable",
            "port": port_id,
            "enabled": True,
            "meraki": body,
        }), 200
    return jsonify(body), code


@app.route("/port/<port_id>/disable", methods=["POST", "GET"])
@require_auth
def disable_port(port_id: str):
    """Disable a switch port."""
    code, body = update_port(port_id, False)
    if code == 200:
        logger.info("Port %s DISABLED by %s", port_id, request.remote_addr)
        return jsonify({
            "status": "success",
            "action": "disable",
            "port": port_id,
            "enabled": False,
            "meraki": body,
        }), 200
    return jsonify(body), code


@app.route("/port/<port_id>/status", methods=["GET"])
@require_auth
def port_status(port_id: str):
    """Return current port configuration."""
    code, body = get_port_status(port_id)
    if code == 200:
        return jsonify({
            "status": "success",
            "port": port_id,
            "enabled": body.get("enabled"),
            "name": body.get("name"),
            "type": body.get("type"),
            "vlan": body.get("vlan"),
            "poeEnabled": body.get("poeEnabled"),
            "full": body,
        }), 200
    return jsonify(body), code


# ---------------------------------------------------------------------------
# Local development entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # For local testing only – do NOT use in production
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
