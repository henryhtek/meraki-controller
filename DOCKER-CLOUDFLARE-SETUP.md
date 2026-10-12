# Docker + Cloudflare Tunnel Deployment Guide

**App version:** 1.1.0

Two complete ways to make the **Meraki API Gateway** reachable over public HTTPS for voice control (**IFTTT**, **Google Smart Home**, **Alexa**, or **Home Assistant** — see `VOICE-SETUP.md`).

- **Option A** – Raspberry Pi + Docker + Cloudflare Tunnel  
  - **A-NPM** – Behind Nginx Proxy Manager (on the `outside` network)  
  - **A-Host** – Without NPM (both containers use `network_mode: host`)
- **Option B** – Free public host (PythonAnywhere / Render / Railway)

---

## Step-by-step checklist (Option A – Raspberry Pi)

Follow in order. Details for each step are in the sections below.

| Step | What to do | Section |
|------|------------|---------|
| 1 | Confirm prerequisites (Docker, Cloudflare account, optional NPM) | A.1 |
| 2 | Create `~/meraki-controller` and copy project files | A.2 |
| 3 | Create `.env` (`MERAKI_API_KEY`, `SWITCH_SERIAL`, `AUTH_TOKEN`) | A.2 |
| 4 | Choose networking: **NPM (`outside`)** or **host network** | A.3 |
| 5 | `docker compose build && docker compose up -d` | A.3 |
| 6 | Create Cloudflare **named tunnel**, put token in `.env`, restart `cloudflared` | A.4 |
| 7 | Add **Public Hostname** (→ NPM or `http://127.0.0.1:8080`) | A.5 |
| 8 | If using NPM: create Proxy Host → `meraki-api-gateway:8080` | A.6 |
| 9 | Test public URL with `curl` (and internal tests if needed) | A.7 |
| 10 | Fix issues using the troubleshooting table | A.8 |
| 11 | Enable Docker on boot | A.9 |
| 12 | Configure voice (`VOICE-SETUP.md` / `IFTTT-SETUP.md`) | After public URL works |

**Domain note:** A **named** Cloudflare tunnel with a stable hostname needs a domain on your Cloudflare account. For a temporary test URL without a domain, use a Quick Tunnel (`cloudflared tunnel --url http://127.0.0.1:8080`) — URL changes on restart; not ideal for permanent voice.

---

## Architecture comparison

### With Nginx Proxy Manager (recommended if you already run NPM)

```
┌─────────────────────────────────────────────────────────────┐
│          Internet / IFTTT / Google / Alexa                  │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              Cloudflare Edge (Public Hostname)              │
│         meraki.yourdomain.com  →  Tunnel                    │
└────────────────────────────┬────────────────────────────────┘
                             │ encrypted tunnel
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi (Ubuntu)                    │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Docker network: outside                  │  │
│  │              (bridge 172.20.0.0/16)                   │  │
│  │                                                       │  │
│  │  ┌─────────────┐     ┌──────────────────┐             │  │
│  │  │ cloudflared │────▶│ Nginx Proxy      │             │  │
│  │  │             │     │ Manager (NPM)    │             │  │
│  │  └─────────────┘     │ :80 / :443       │             │  │
│  │                      └────────┬─────────┘             │  │
│  │                               │                       │  │
│  │                               │ http://meraki-api-    │  │
│  │                               │ gateway:8080          │  │
│  │                               ▼                       │  │
│  │                      ┌──────────────────┐             │  │
│  │                      │ meraki-api-      │             │  │
│  │                      │ gateway          │             │  │
│  │                      │ (Flask :8080)    │             │  │
│  │                      └──────────────────┘             │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Traffic flow (with NPM)**

1. Voice cloud / IFTTT → Cloudflare Public Hostname (HTTPS)
2. Cloudflare Tunnel → `cloudflared`
3. `cloudflared` → Nginx Proxy Manager (`http://<npm-container>:80`)
4. NPM → `meraki-api-gateway:8080`
5. Gateway → Cisco Meraki Dashboard API

---

### Without NPM (both containers use host network)

```
┌─────────────────────────────────────────────────────────────┐
│          Internet / IFTTT / Google / Alexa                  │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              Cloudflare Edge (Public Hostname)              │
│         meraki.yourdomain.com  →  Tunnel                    │
└────────────────────────────┬────────────────────────────────┘
                             │ encrypted tunnel
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi (Ubuntu)                    │
│                                                             │
│   Host network (shared with the OS)                         │
│                                                             │
│   ┌─────────────┐          ┌──────────────────┐             │
│   │ cloudflared │─────────▶│ meraki-api-      │             │
│   │             │          │ gateway          │             │
│   └─────────────┘          │ (Flask :8080)    │             │
│                            └──────────────────┘             │
│                                                             │
│   Cloudflare Public Hostname service URL:                   │
│   http://127.0.0.1:8080                                     │
└─────────────────────────────────────────────────────────────┘
```

**Traffic flow (without NPM)**

1. Voice cloud / IFTTT → Cloudflare Public Hostname (HTTPS)
2. Cloudflare Tunnel → `cloudflared` (host network)
3. `cloudflared` → `http://127.0.0.1:8080` (Meraki API Gateway on host network)
4. Gateway → Cisco Meraki Dashboard API

---

## Side-by-side: what changes

| Setting | With NPM (`outside` network) | Without NPM (host network) |
|---------|------------------------------|----------------------------|
| `meraki-api-gateway` network | `outside` (external) | `network_mode: host` |
| `cloudflared` network | `outside` (external) | `network_mode: host` |
| Publish port 8080 | No | No (host mode already binds to host) |
| Cloudflare Public Hostname URL | `http://<npm-container-name>:80` | `http://127.0.0.1:8080` |
| NPM Proxy Host needed? | Yes → forward to `meraki-api-gateway:8080` | No |
| SSL termination | NPM (Let’s Encrypt) or Cloudflare | Cloudflare only |
| Best when | You already run NPM | You want the simplest possible setup |

---

## Option A – Raspberry Pi + Docker + Cloudflare Tunnel

### A.1 Prerequisites

- Raspberry Pi running Ubuntu Server (or Raspberry Pi OS)
- Docker + Docker Compose already installed
- Free Cloudflare account
- **With NPM:** Nginx Proxy Manager already running on the Docker network named `outside` (subnet `172.20.0.0/16`)
- **Without NPM:** nothing extra required

### A.2 Project files on the Pi

Use the project folder **`meraki-controller`** (same name as the Compose project in `docker-compose.yml`).

**Option 1 – Copy files manually**

```bash
mkdir -p ~/meraki-controller
cd ~/meraki-controller
```

Copy these files from the project into `~/meraki-controller`:

- `app.py`
- `requirements.txt`
- `Dockerfile`
- `docker-compose.yml`
- `.env.example`
- (optional) `README.md`, `DOCKER-CLOUDFLARE-SETUP.md`, `IFTTT-SETUP.md`

**Option 2 – Clone from GitHub** (if you published the repo)

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/meraki-controller.git
cd meraki-controller
```

**Create the secrets file**

```bash
cd ~/meraki-controller
cp .env.example .env
nano .env
```

Fill in at least:

```env
MERAKI_API_KEY=your_meraki_api_key
SWITCH_SERIAL=Q2XX-XXXX-XXXX
AUTH_TOKEN=long_random_secret_at_least_32_chars
CLOUDFLARE_TUNNEL_TOKEN=
```

All later commands in Option A assume you are in:

```bash
cd ~/meraki-controller
```

### A.3 Choose your networking mode

#### A.3.1 – With NPM (default `docker-compose.yml`)

The provided `docker-compose.yml` already joins the external network `outside`.

```bash
docker compose build
docker compose up -d
```

Verify:

```bash
docker network inspect outside --format '{{range .Containers}}{{.Name}} {{end}}'
```

You should see `meraki-api-gateway`, `cloudflared`, and your NPM container.

#### A.3.2 – Without NPM (host network)

Edit `docker-compose.yml` so both services use host networking.  
**What to change:**

| Item | Change to |
|------|-----------|
| `networks:` / `outside` | Remove the `networks:` blocks and the top-level `networks:` section |
| `meraki-api-gateway` | Add `network_mode: host` |
| `cloudflared` | Add `network_mode: host` |
| `ports:` | Keep commented / removed (host mode binds directly) |
| `depends_on` | Can stay |

Example host-network `docker-compose.yml`:

```yaml
name: meraki-controller

services:
  meraki-api-gateway:
    build: .
    image: meraki-api-gateway:latest
    container_name: meraki-api-gateway
    restart: unless-stopped
    network_mode: host
    env_file:
      - .env
    environment:
      - PORT=8080

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: cloudflared
    restart: unless-stopped
    network_mode: host
    command: tunnel --no-autoupdate run --token ${CLOUDFLARE_TUNNEL_TOKEN}
    environment:
      - CLOUDFLARE_TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}
    depends_on:
      - meraki-api-gateway
```

Then:

```bash
docker compose build
docker compose up -d
```

Test locally:

```bash
curl http://127.0.0.1:8080/health
```

### A.4 Create a Cloudflare Tunnel

1. Go to [https://one.dash.cloudflare.com](https://one.dash.cloudflare.com)
2. Zero Trust → Networks → Tunnels → Create a tunnel
3. Choose **Cloudflared**
4. Name it (e.g. `meraki-pi`)
5. Copy the **token** shown (or the install command that contains the token)
6. Put the token into `.env`:

```env
CLOUDFLARE_TUNNEL_TOKEN=eyJ...your_token...
```

7. Restart cloudflared:

```bash
docker compose up -d cloudflared
```

### A.5 Add a Public Hostname

In the tunnel configuration:

| Field | With NPM | Without NPM |
|-------|----------|-------------|
| Subdomain | e.g. `meraki` | e.g. `meraki` |
| Domain | your domain on Cloudflare | your domain on Cloudflare |
| Path | (leave empty) | (leave empty) |
| Type | HTTP | HTTP |
| URL | `http://npm-container-name:80` (or the IP of NPM on `outside`) | `http://127.0.0.1:8080` |

Save. Cloudflare will provision the hostname.

### A.6 NPM Proxy Host (only if using NPM)

1. In Nginx Proxy Manager UI → Proxy Hosts → Add Proxy Host
2. Domain Names: the same hostname you set in Cloudflare (e.g. `meraki.yourdomain.com`)
3. Scheme: `http`
4. Forward Hostname / IP: `meraki-api-gateway`
5. Forward Port: `8080`
6. Cache Assets: Off
7. Block Common Exploits: On (optional)
8. Websockets Support: Off (not required for this API)
9. SSL: can stay off if Cloudflare terminates HTTPS (or use Cloudflare Full/Strict + NPM cert if desired)

Save.

### A.7 Test

**Public health check**

```bash
curl -s https://meraki.yourdomain.com/health
```

Expected: JSON with `"status": "ok"` (and version).

**Enable / disable / status (replace token and port)**

```bash
# Enable port 7
curl -s -X POST "https://meraki.yourdomain.com/port/7/enable?token=YOUR_AUTH_TOKEN"

# Disable port 7
curl -s -X POST "https://meraki.yourdomain.com/port/7/disable?token=YOUR_AUTH_TOKEN"

# Status
curl -s "https://meraki.yourdomain.com/port/7/status?token=YOUR_AUTH_TOKEN"
```

**Internal (on the Pi, NPM path)**

```bash
# From a container on `outside`, or via host if you know the IP
curl -s http://meraki-api-gateway:8080/health
```

**Internal (host network path)**

```bash
curl -s http://127.0.0.1:8080/health
```

### A.8 Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| 401 Unauthorized | Wrong or missing `AUTH_TOKEN` | Match query `token=` to `.env` `AUTH_TOKEN` |
| 403 Forbidden | Port not in `ALLOWED_PORTS` | Add the port number to `ALLOWED_PORTS` in `.env` and recreate container |
| 502 / tunnel errors | cloudflared not running or wrong URL | Check `docker logs cloudflared`; Public Hostname URL must reach NPM or 127.0.0.1:8080 |
| Connection refused on 8080 | Gateway not up / wrong network | `docker compose ps`; verify network mode matches guide |
| NPM 502 | Wrong upstream name/port | Forward to `meraki-api-gateway:8080` on the same Docker network |
| Cloudflare 1033 / 502 | Tunnel offline | Restart `cloudflared`; confirm token |
| Health works, enable fails | Meraki API key / serial / port | Check Meraki Dashboard API key scope and switch serial |

Logs:

```bash
docker logs meraki-api-gateway --tail 100
docker logs cloudflared --tail 100
```

### A.9 Enable Docker on boot

```bash
sudo systemctl enable docker
```

---

## Option B – Free public host (no Raspberry Pi required)

Deploy the same Flask app on a free PaaS. You still need a stable HTTPS URL for voice.

### B.1 PythonAnywhere

1. Create a free account at pythonanywhere.com
2. Upload `app.py` and `requirements.txt` (or use a Git clone if supported)
3. Create a virtualenv and install requirements
4. Configure a WSGI file to import the Flask `app`
5. Set environment variables: `MERAKI_API_KEY`, `SWITCH_SERIAL`, `AUTH_TOKEN`, `ALLOWED_PORTS`
6. Reload the web app
7. Use the provided `https://YOUR_USERNAME.pythonanywhere.com` URL

### B.2 Render / Railway

1. Connect the GitHub repo (or deploy from Dockerfile)
2. Set env vars from `.env.example`
3. Use the generated HTTPS URL

**Note:** Free tiers sleep after inactivity; first request after sleep can be slow. Named Cloudflare Tunnel on a Pi is usually more reliable for always-on voice.

---

## What the Compose stack creates

With the default `docker-compose.yml` (project name `meraki-controller`):

| Resource | Name |
|----------|------|
| Compose project | `meraki-controller` |
| Gateway container | `meraki-api-gateway` |
| Tunnel container | `cloudflared` |
| Image | `meraki-api-gateway:latest` |
| Network | external `outside` |

---

## Security notes

- Never commit `.env` (it is in `.gitignore`)
- Use a long random `AUTH_TOKEN` (≥ 32 characters)
- Restrict `ALLOWED_PORTS` to only the ports you need
- Prefer Cloudflare Tunnel over opening ports on your router
- Rotate Meraki API keys if they are ever exposed

---

## Next steps

When the public URL responds correctly to `/health` and port enable/disable:

1. Open **`VOICE-SETUP.md`** for Google / Alexa / Home Assistant options
2. Or **`IFTTT-SETUP.md`** if you use IFTTT applets
