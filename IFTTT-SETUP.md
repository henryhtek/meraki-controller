# IFTTT Setup for Google Assistant & Amazon Alexa

This guide shows how to create IFTTT applets that call your **Meraki API Gateway** webhook, and how to use shorter voice commands with Google Home or Alexa Routines.

The same backend works for both platforms. Only the IFTTT trigger differs.

**Prerequisite:** You already have a working public HTTPS URL for the Flask app  
(see `DOCKER-CLOUDFLARE-SETUP.md`).

**Other voice options (no IFTTT):** Google Smart Home, Alexa webhook/virtual skills, and Home Assistant — see **`VOICE-SETUP.md`**.  
Note: IFTTT Free is limited; Webhooks often requires **Pro**.

Example public URL used below:

```
https://meraki.yourdomain.com
```

---

## Version check (recommended before creating applets)

```bash
curl https://meraki.yourdomain.com/health
```

You should see a response that includes the app version, for example:

```json
{"status": "ok", "version": "1.1.0", "meraki_key_set": true, ...}
```

Both `GET /` and `GET /health` return the `"version"` field for deployment tracking.

---

## 1. Connect your voice assistant to IFTTT (do this once per platform)

### Google Home / Google Assistant

1. Open the **Google Home** app on your phone.
2. Tap your profile picture → **Home settings** → **Works with Google**.
3. Search for **IFTTT** and link / authorize your account.
4. Restart the Google Home app.

### Amazon Alexa

1. Open the **Amazon Alexa** app on your phone.
2. Go to **More** → **Skills & Games** → search for **IFTTT**.
3. Enable the IFTTT skill and link your IFTTT account.
4. Alternatively, link from the IFTTT side: IFTTT → Services → Alexa → Connect.

---

## 2. Create an IFTTT Applet – Google Assistant (Enable)

1. Go to [https://ifttt.com/create](https://ifttt.com/create)
2. Click the **Classic** tab.
3. **If This**
   - Search for **Google Assistant** (or Google Assistant V2)
   - Choose the trigger **Activate scene**
   - Scene name example: `Enable Meraki Port 7`
   - Create trigger
4. **Then That**
   - Search for **Webhooks**
   - Choose **Make a web request**
   - Fill in:

| Field                | Value |
|----------------------|-------|
| URL                  | `https://meraki.yourdomain.com/port/7/enable?token=YOUR_AUTH_TOKEN` |
| Method               | `POST` |
| Content Type         | `application/json` (or leave blank) |
| Additional Headers   | leave empty |
| Body                 | leave empty |

5. Create action → Finish.

---

## 3. Create an IFTTT Applet – Google Assistant (Disable)

Repeat the same steps with:

- Scene name: `Disable Meraki Port 7`
- URL: `https://meraki.yourdomain.com/port/7/disable?token=YOUR_AUTH_TOKEN`

---

## 4. Create an IFTTT Applet – Amazon Alexa (Enable)

1. Go to [https://ifttt.com/create](https://ifttt.com/create)
2. Click the **Classic** tab.
3. **If This**
   - Search for **Amazon Alexa**
   - Choose the trigger **Say a specific phrase** (or similar phrase trigger available in your region)
   - Phrase example: `enable meraki port 7`
   - Create trigger
4. **Then That**
   - Search for **Webhooks**
   - Choose **Make a web request**
   - Use the **same URL** as the Google enable applet:

```
https://meraki.yourdomain.com/port/7/enable?token=YOUR_AUTH_TOKEN
```

5. Method: `POST` → Create action → Finish.

You will then say:

> “Alexa, trigger enable meraki port 7”

(Exact wording depends on the Alexa IFTTT trigger phrasing shown in the applet.)

---

## 5. Create an IFTTT Applet – Amazon Alexa (Disable)

Same as above, with:

- Phrase: `disable meraki port 7`
- URL: `https://meraki.yourdomain.com/port/7/disable?token=YOUR_AUTH_TOKEN`

---

## 6. Create more ports

Create one pair of applets (enable + disable) per port, for each voice platform you use.

| Platform | Example trigger | Flask path |
|----------|-----------------|------------|
| Google | Scene: `Enable Meraki Port 7` | `/port/7/enable?...` |
| Google | Scene: `Disable Meraki Port 7` | `/port/7/disable?...` |
| Alexa | Phrase: `enable meraki port 7` | `/port/7/enable?...` |
| Alexa | Phrase: `disable meraki port 7` | `/port/7/disable?...` |

---

## 7. Shorter voice commands

### Google Home Routines

1. Open the **Google Home** app → **Routines** → **+ New**.
2. **Starter** → Voice command (e.g. `Turn on port 7`).
3. **Action** → **Adjust Home devices** / **Activate scene** → select the IFTTT scene (e.g. `Enable Meraki Port 7`).
4. Save.

Say: “Hey Google, turn on port 7”.

### Alexa Routines

1. Open the **Amazon Alexa** app → **More** → **Routines** → **+**.
2. **When this happens** → Voice → e.g. `turn on port 7`.
3. **Add action** → **Skills** / **IFTTT** or choose the action that runs your IFTTT applet, depending on what Alexa exposes in your region.
4. Alternatively, keep using the IFTTT phrase trigger directly (“Alexa, trigger enable meraki port 7”).

---

## 8. Test the webhook before relying on voice

```bash
curl -X POST "https://meraki.yourdomain.com/port/7/enable?token=YOUR_AUTH_TOKEN"
curl -X POST "https://meraki.yourdomain.com/port/7/disable?token=YOUR_AUTH_TOKEN"
curl "https://meraki.yourdomain.com/port/7/status?token=YOUR_AUTH_TOKEN"
curl "https://meraki.yourdomain.com/health"
```

You should receive JSON with `"status": "success"` (or `"ok"` for health) and a `"version"` field on health/index.

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---------|--------------|-----|
| IFTTT says success but port does not change | Wrong token or URL | Test the exact public URL with `curl` (see below) |
| 401 Unauthorized | Token mismatch | Check `AUTH_TOKEN` in `.env` and in the IFTTT URL |
| Scene does not appear in Google Home | IFTTT not linked | Re-link IFTTT under “Works with Google” |
| Alexa does not run the applet | IFTTT skill not enabled / account not linked | Enable IFTTT skill in the Alexa app and re-link |
| Routine does nothing | Wrong scene / phrase selected | Match the exact IFTTT scene name or phrase |
| Public URL unreachable | Tunnel / NPM / DNS issue | See **A.7 Test** and **A.8 Troubleshooting** in `DOCKER-CLOUDFLARE-SETUP.md` |

**Public URL curl tests** (same path IFTTT uses):

```bash
curl https://meraki.yourdomain.com/health
curl -X POST "https://meraki.yourdomain.com/port/7/enable?token=YOUR_AUTH_TOKEN"
curl -X POST "https://meraki.yourdomain.com/port/7/disable?token=YOUR_AUTH_TOKEN"
curl "https://meraki.yourdomain.com/port/7/status?token=YOUR_AUTH_TOKEN"
```

In NPM mode, do **not** rely on `curl http://127.0.0.1:8080` from the Pi — that port is not published. Use the public URL or the internal Docker network tests in `DOCKER-CLOUDFLARE-SETUP.md`.

---

## Next steps

- Add more ports for Google and/or Alexa
- Use scenes/phrases inside more complex Routines (time-based, presence, etc.)
- Optionally restrict which ports are allowed via `ALLOWED_PORTS` in the `.env` file
