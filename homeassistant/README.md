# Home Assistant samples (Option D) — multiple Meraki ports

| File | Purpose |
|------|---------|
| `docker-compose.yml` | HA on Docker network `outside` |
| `configuration.example.yaml` | Ports **7** and **8**: combined switches, sensors, error scripts |

Full steps: **`VOICE-SETUP.md` → Option D**.

### Add another port (e.g. 24)

1. Add three lines to `secrets.yaml` (`meraki_port_24_on_url`, `_off_url`, `_status_url`).
2. Copy the port **8** blocks in `configuration.yaml` and replace `8` → `24`.
3. Set gateway `ALLOWED_PORTS=7,8` (or leave empty).
4. `docker restart homeassistant`

### Entities per port N

| Entity | Role |
|--------|------|
| `switch.meraki_port_N` | Combined on/off in the UI |
| `sensor.meraki_port_N_enabled` | Status from gateway |
| `script.meraki_port_N_enable` / `_disable` | REST + failure notifications |

### HA 2026.8+

- Reverse proxy: **Settings → System → Network → HTTP server**
- Mobile app: keep `default_config:` or add `mobile_app:`
