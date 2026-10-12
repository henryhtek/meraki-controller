# Meraki API Gateway for Google Home & Amazon Alexa

**Version:** 1.1.0

Control Cisco Meraki devices and networks with **Google Assistant / Google Home** and **Amazon Alexa** using a small authenticated Flask webhook.

## Summary

Meraki API Gateway is a small authenticated Flask webhook that lets you enable and disable Cisco Meraki switch ports with voice commands. Deploy it on a Raspberry Pi with Docker and Cloudflare Tunnel (with or without Nginx Proxy Manager), or on a free public host. The same public HTTPS URL can be used by IFTTT, Google Smart Home, Alexa skills, or Home Assistant.

## Stack

```text
Voice front-end (choose one)
  ├─ IFTTT (Google Assistant / Alexa)     → often needs Pro for Webhooks
  ├─ Google Smart Home (Cloud Function) → free-tier path, no IFTTT
  ├─ Alexa virtual switch / custom skill  → free tiers available
  └─ Home Assistant rest_command         → free, self-hosted
        ↓
  HTTPS public URL (Cloudflare Tunnel or public host)
        ↓
  meraki-api-gateway (this project)
        ↓
  Cisco Meraki Dashboard API
```

## Project structure

| File | Purpose |
|------|---------|
| `app.py` | Flask webhook application (Meraki API Gateway) |
| `Dockerfile` | Multi-arch Docker image (works on Raspberry Pi ARM) |
| `docker-compose.yml` | Runs `meraki-api-gateway` + Cloudflare Tunnel |
| `.env.example` | Environment variable template |
| `DOCKER-CLOUDFLARE-SETUP.md` | Deploy: Docker, Cloudflare Tunnel, NPM, uninstall |
| `VOICE-SETUP.md` | Voice options: IFTTT, Google Smart Home, Alexa, Home Assistant |
| `IFTTT-SETUP.md` | Detailed IFTTT applets for Google Assistant & Alexa |
| `homeassistant/` | Sample HA Docker Compose + config snippets (Option D) |

## Deployment

See **`DOCKER-CLOUDFLARE-SETUP.md`**:

- **Option A** – Raspberry Pi + Docker + Cloudflare Tunnel (NPM or host network)
- **Option B** – Free public host (PythonAnywhere / Render / Railway)

Project folder on the Pi: `~/meraki-controller`

## Voice setup

See **`VOICE-SETUP.md`** for all options and a comparison table.

| Path | Doc |
|------|-----|
| IFTTT (Google + Alexa) | `IFTTT-SETUP.md` + `VOICE-SETUP.md` Option A |
| Google Smart Home (no IFTTT) | `VOICE-SETUP.md` Option B |
| Alexa without IFTTT | `VOICE-SETUP.md` Option C |
| Home Assistant | `VOICE-SETUP.md` Option D |

## Version check

```bash
curl https://meraki.yourdomain.com/health
```

Example:

```json
{"status": "ok", "version": "1.1.0", "meraki_key_set": true, ...}
```

Both `GET /` and `GET /health` return the `"version"` field.

## Quick start

1. Deploy the gateway (`DOCKER-CLOUDFLARE-SETUP.md`) → public HTTPS URL  
2. Test with `curl`  
3. Choose a voice path (`VOICE-SETUP.md`)  
4. For IFTTT only: follow `IFTTT-SETUP.md`  
