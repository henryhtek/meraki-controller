# Voice setup options for Meraki API Gateway

Control Cisco Meraki switch ports by voice using **Google Assistant / Google Home** and/or **Amazon Alexa**. All options call the same backend:

```text
Voice front-end  →  HTTPS  →  meraki-api-gateway  →  Meraki Dashboard API
```

**Before voice:** deploy the gateway and obtain a **stable public HTTPS URL**  
(see **`DOCKER-CLOUDFLARE-SETUP.md`** — named Cloudflare Tunnel + domain recommended).

---

## Recommended order

1. Deploy gateway + public URL (`DOCKER-CLOUDFLARE-SETUP.md`)
2. Test with `curl` (health + enable/disable)
3. Pick a voice option below
4. Complete that option’s steps
5. Test by voice

---

## Which option should I use?

| Option | Voice | Cost | Difficulty | Best when |
|--------|--------|------|------------|-----------|
| **A – IFTTT** | Google + Alexa | Free limited; Webhooks often **Pro** | Low | You already pay for IFTTT Pro or only need 1–2 applets |
| **B – Google Smart Home** | Google only | Free tier (Google Cloud) | Higher | Free Google voice; ports as real switches in Google Home |
| **C – Alexa (no IFTTT)** | Alexa only | Free tiers available | Low–medium | Free Alexa voice without IFTTT |
| **D – Home Assistant** | Optional | Free (self-hosted) | Medium | You already run HA on the Pi |

---

## Option A – IFTTT (Google Assistant & Alexa)

### Steps

1. Confirm public URL works:
   ```bash
   curl https://YOUR_PUBLIC_URL/health
   ```
2. Open **`IFTTT-SETUP.md`** and follow it in order:
   - Link Google Home and/or Alexa to IFTTT
   - Create enable applet (scene/phrase → Webhooks POST to `/port/{id}/enable?token=...`)
   - Create disable applet
   - Optional: Google Home / Alexa Routines for shorter phrases
3. Test by voice, then check Meraki Dashboard / `curl` status

### Notes

- Free plan: few active Applets (often ~2)
- **Webhooks** is often a Pro feature — confirm in the IFTTT editor
- Same public URL works for Google and Alexa applets

---

## Option B – Google Smart Home (free path, no IFTTT)

Ports appear as **switches** in the Google Home app:

> “Hey Google, turn on Port 7”

### Architecture

```text
Google Assistant
    → Your Smart Home fulfillment (Cloud Function / Cloud Run)
    → HTTPS to meraki-api-gateway
    → Meraki API
```

### Step-by-step

**B1 – Prerequisites**

1. Public HTTPS URL of `meraki-api-gateway` working (`/health` returns ok)
2. Google account
3. Google Cloud project (free tier is enough for personal use)

**B2 – Create the Cloud project & enable APIs**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (e.g. `meraki-voice`)
3. Enable APIs used by Smart Home / HomeGraph as required by current Google Home developer docs
4. Note the project ID

**B3 – Create a Smart Home / Cloud-to-cloud integration**

1. Open [Google Home Developer Console](https://developers.home.google.com/) (or Actions console path documented by Google for cloud-to-cloud)
2. Create a **Cloud-to-cloud** / Smart Home integration linked to your Cloud project
3. Set display name (e.g. “Meraki Ports”)

**B4 – Implement fulfillment**

1. Deploy a small HTTPS service (Cloud Functions or Cloud Run) that handles:

| Intent | What to do |
|--------|------------|
| **SYNC** | Return one device per port (or a fixed list) |
| **QUERY** | Optional: `GET /port/{id}/status?token=...` or report last known state |
| **EXECUTE** | On `action.devices.commands.OnOff`: call enable or disable on the gateway |

2. Device fields (each port):

| Field | Example |
|-------|---------|
| `id` | `meraki-port-5` |
| `type` | `action.devices.types.SWITCH` |
| `traits` | `action.devices.traits.OnOff` |
| `name` | `Port 7` / nicknames as you like |

3. Map EXECUTE:

| `params.on` | Gateway call |
|-------------|--------------|
| `true` | `POST https://YOUR_PUBLIC_URL/port/7/enable?token=YOUR_AUTH_TOKEN` |
| `false` | `POST https://YOUR_PUBLIC_URL/port/7/disable?token=YOUR_AUTH_TOKEN` |

4. Store `YOUR_PUBLIC_URL` and `YOUR_AUTH_TOKEN` as environment secrets in Cloud Functions / Cloud Run — do not hard-code in public repos

**B5 – Account linking**

1. Configure OAuth account linking as required by Google for personal testing (simplified/mock OAuth is common in codelabs for development)
2. Ensure the fulfillment URL is set in the integration (HTTPS)

**B6 – Test in Google Home**

1. On your phone, open the **Google Home** app
2. Link the service under Works with Google / your test integration (follow current console “test” instructions)
3. Sync devices if prompted
4. Confirm switches appear (e.g. Port 7)
5. Toggle in the app, then by voice: “Hey Google, turn on Port 7”
6. Verify with:
   ```bash
   curl "https://YOUR_PUBLIC_URL/port/7/status?token=YOUR_AUTH_TOKEN"
   ```

**B7 – Optional: routines**

Create a Google Home Routine that turns the switch on/off for a shorter phrase.

### Gateway URLs (reference)

```text
POST https://YOUR_PUBLIC_URL/port/7/enable?token=YOUR_AUTH_TOKEN
POST https://YOUR_PUBLIC_URL/port/7/disable?token=YOUR_AUTH_TOKEN
GET  https://YOUR_PUBLIC_URL/port/7/status?token=YOUR_AUTH_TOKEN
```

### Pros / cons

| Pros | Cons |
|------|------|
| No IFTTT | More setup than IFTTT |
| Native Google Home devices & routines | You maintain fulfillment code |
| Free within free-tier quotas | Account linking required |

### Official references

- [Google Home Cloud-to-cloud](https://developers.home.google.com/cloud-to-cloud)
- [OnOff trait](https://developers.home.google.com/cloud-to-cloud/traits/onoff)
- Smart Home codelabs (washer / cloud fulfillment) — adapt to call **your** gateway instead of a virtual device

---

## Option C – Amazon Alexa without IFTTT

### C.1 Virtual switch / webhook-style skill (easiest)

**Steps**

1. Confirm gateway URL:
   ```bash
   curl https://YOUR_PUBLIC_URL/health
   ```
2. In the Alexa app → **Skills** → search for a skill that supports **virtual devices** or **custom webhooks** (names change over time; choose one that can call an arbitrary HTTPS URL)
3. Enable the skill and complete account linking if asked
4. Create a virtual device / action per port, for example:
   - Name: `Port 7`
   - On URL: `https://YOUR_PUBLIC_URL/port/7/enable?token=YOUR_AUTH_TOKEN`
   - Off URL: `https://YOUR_PUBLIC_URL/port/7/disable?token=YOUR_AUTH_TOKEN`
   - Method: POST (or GET if the skill only supports GET and your gateway allows GET)
5. Discover devices in the Alexa app
6. Test: “Alexa, turn on Port 7”
7. Confirm with Meraki or:
   ```bash
   curl "https://YOUR_PUBLIC_URL/port/7/status?token=YOUR_AUTH_TOKEN"
   ```

### C.2 Custom Alexa Skill (AWS free tier)

**Steps**

1. Create an AWS account; use Lambda free tier
2. Create an Alexa Skill (custom or smart home model) in the Alexa Developer Console
3. Point the skill endpoint at a Lambda function
4. In Lambda, on the relevant intent/directive:
   - Call your gateway enable/disable URLs with `fetch` / `https` / `axios`
5. Enable the skill in developer mode on your account
6. Discover devices / invoke the utterance
7. Test and check gateway logs / Meraki

**Pros:** No IFTTT, works with Echo.  
**Cons:** More work than a pre-built webhook skill; stay in dev mode or publish if required.

### Gateway URLs

```text
.../port/{id}/enable?token=...
.../port/{id}/disable?token=...
```

---

## Option D – Home Assistant (Docker + Meraki gateway)

Sample files are in the project folder **`homeassistant/`**:

| File | Purpose |
|------|---------|
| `homeassistant/docker-compose.yml` | HA container (joins network `outside`) |
| `homeassistant/configuration.example.yaml` | `rest_command`, template switch, status sensor |
| `homeassistant/README.md` | Short copy instructions |

### D1 – Deploy Home Assistant with Docker

```bash
mkdir -p ~/homeassistant/config
cp /path/to/meraki-controller/homeassistant/docker-compose.yml ~/homeassistant/
cd ~/homeassistant
docker compose up -d
```

- UI: `http://PI_IP:8123` (use **direct** port first, not NPM, until proxy is configured)
- Complete onboarding in the browser
- Ensure network `outside` exists if you use the sample compose (same as Meraki gateway + NPM)

**Network choices**

| HA network | How to call Meraki API Gateway |
|------------|--------------------------------|
| `outside` (sample compose) | `http://meraki-api-gateway:8080/...` or public HTTPS URL |
| `network_mode: host` | `http://127.0.0.1:8080/...` (if gateway also host) or public URL |
| Any | Always works: `https://YOUR_PUBLIC_URL/...` |

### D1b – Reverse proxy (NPM) on Home Assistant 2026.8+

Starting with **Home Assistant 2026.8**, the `http:` block in `configuration.yaml` is **deprecated**.  
Reverse-proxy settings live in the **UI** (stored under `/config/.storage/http`).  
A YAML `http:` section is often **ignored at runtime**, which causes:

```text
HTTP integration is not set-up for reverse proxies
```

even when `use_x_forwarded_for` appears in `configuration.yaml`.

#### Preferred: configure in the UI

1. Open HA **directly** (bypass NPM): `http://PI_IP:8123`
2. Go to **Settings → System → Network**
3. Open **HTTP server**
4. Enable **Trust X-Forwarded-For**
5. Under **Trusted proxies**, add:
   - `172.20.0.6` (your NPM container IP from the error log)
   - `172.20.0.0/16` (Docker `outside` network)
6. Save / **confirm** within the time window if HA asks (settings can roll back if not confirmed)
7. **Remove** any `http:` block from `configuration.yaml`
8. Restart:

```bash
docker restart homeassistant
```

9. Test via NPM: `https://ha.yourlocal/`

#### If locked out behind NPM only: edit `.storage/http`

```bash
docker stop homeassistant
# Host path is typically:
#   ~/homeassistant/config/.storage/http
# Edit JSON: enable trust X-Forwarded-For; add 172.20.0.6 and 172.20.0.0/16
docker start homeassistant
```

#### Remove deprecated YAML

Delete the entire `http:` section from `configuration.yaml`, then restart HA.  
Do **not** rely on YAML for reverse-proxy settings on 2026.8+.

### D2 – secrets and configuration

1. Copy the example:

```bash
cp /path/to/meraki-controller/homeassistant/configuration.example.yaml ~/homeassistant/config/configuration.yaml
```

2. Create `secrets.yaml` (or use the UI secrets):

```yaml
meraki_auth_token: "your_long_auth_token"
meraki_gateway_url: "http://meraki-api-gateway:8080"   # or https://YOUR_PUBLIC_URL
```

3. Ensure `default_config:` (or `mobile_app:`) is present so the mobile app works.

4. Restart HA after editing YAML:

```bash
docker restart homeassistant
```

### D3 – rest_command + template switches (ports 7 and 8)

The example config defines:

- `rest_command.meraki_port_enable` / `meraki_port_disable`
- REST sensors for port status (`on` / `off`)
- Modern **template** switches for Port 7 and Port 8
- Scripts that call the rest commands, wait, refresh the sensor, and show a **persistent_notification** on failure

After restart, the switches appear under **Settings → Devices & Services → Entities** (or the Overview dashboard).

### D4 – Voice via Home Assistant

- Expose the template switches to Google Assistant / Alexa using HA’s native integrations (or Nabu Casa)
- Or use HA routines / automations that call the same scripts

### D5 – Troubleshooting HA + gateway

| Issue | Fix |
|-------|-----|
| 400 Bad Request behind NPM | Trusted proxies in UI (D1b); full restart |
| 401 / 403 from gateway | Token mismatch or port not in `ALLOWED_PORTS` |
| Switch state not updating | `force_update: true` on sensor; longer delay + `update_entity` in script |
| Commands not in UI | Check YAML indentation; restart HA (not just reload) |
| Mobile app missing | Ensure `default_config:` or `mobile_app:` |

---

## Quick reference – gateway endpoints

| Action | Method | Path |
|--------|--------|------|
| Health | GET | `/health` |
| Enable port | POST | `/port/{id}/enable?token=...` |
| Disable port | POST | `/port/{id}/disable?token=...` |
| Status | GET | `/port/{id}/status?token=...` |

Replace `{id}` with the switch port number (e.g. `7` or `8`).

---

## Related files

- `DOCKER-CLOUDFLARE-SETUP.md` – deploy gateway + public HTTPS
- `IFTTT-SETUP.md` – IFTTT applets and routines
- `homeassistant/` – Docker + configuration samples for Option D
- `README.md` – project overview
