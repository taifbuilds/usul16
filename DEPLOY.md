# Deploying usul16.com — step by step

**Goal:** put this app live at `https://usul16.com` for the least money and effort.

## The shape of it (why one server)
- **Frontend** = Next.js (needs a small Node process).
- **Backend** = FastAPI reading a **2.4 GB SQLite file** (`eshia_research.db`) + an in-memory
  graph cache → needs a **persistent process with ~2 GB RAM**. This is why serverless
  (Vercel/Netlify functions) can't host it.
- So: **one small VPS runs both**, with **Caddy** in front for routing + automatic HTTPS.
  The DB is read-only in production, so there's no database server to run or pay for.

```
              usul16.com (HTTPS, Caddy)
                     │
        ┌────────────┴─────────────┐
   /api/*  →  FastAPI :8000     everything else → Next.js :3000
        │                            │
   eshia_research.db (2.4 GB on disk)
```

**Cost:** one Hetzner **CX22** (2 vCPU / 4 GB / 40 GB) ≈ **€4.5/mo (~£3.85)**. Domain you already own.
Total ≈ **£4/mo**. (Cheaper alt: Hetzner **CAX11** ARM, ~€3.8/mo — same specs, x86 CX22 is the zero-surprise choice.)

---

## Part A — Server + domain (once, ~10 min)

1. **Create the server.** Sign up at hetzner.com/cloud → New Project → Add Server:
   - Location: **Falkenstein/Nuremberg** (EU, good for UK).
   - Image: **Ubuntu 24.04**.
   - Type: **CX22**.
   - SSH key: paste your public key if you have one (recommended), else use the emailed root password.
   - Create. **Note the server's public IPv4** (e.g. `203.0.113.10`).

2. **Point the domain (Fasthosts).** In the Fasthosts control panel → domain `usul16.com` → DNS /
   "Advanced DNS". Delete any parked/forwarding records, then add two **A records**:
   | Type | Name | Value | TTL |
   |---|---|---|---|
   | A | `@` | `SERVER_IP` | 300 |
   | A | `www` | `SERVER_IP` | 300 |
   DNS can take 5–60 min. Check with `nslookup usul16.com` until it returns your IP.

---

## Part B — Base server setup (SSH in as root)

```bash
ssh root@SERVER_IP          # accept the fingerprint; enter password if no key

# system + basics
apt update && apt -y upgrade
apt -y install git curl ufw build-essential python3-venv python3-dev

# a non-root user to run the app
adduser --disabled-password --gecos "" usul
usermod -aG sudo usul

# firewall: only SSH + web
ufw allow OpenSSH && ufw allow 80 && ufw allow 443 && ufw --force enable

# 2 GB swap (safety for the Next.js build on a 4 GB box)
fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Node 20
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt -y install nodejs

# Caddy (reverse proxy + auto HTTPS)
apt -y install debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt -y install caddy
```

---

## Part C — Get the code + DB onto the server

The 2.4 GB DB is **not** in git, so it's copied separately. Do these **from your Windows PC**
(Git Bash), from the project folder `Shia Hadith Project`.

**1. Ship the code** (small — excludes node_modules/.venv/.git/DB):
```bash
tar czf usul16-code.tgz \
  --exclude=node_modules --exclude=.venv --exclude=.next \
  --exclude='*.db' --exclude=.git \
  web eshia-research
scp usul16-code.tgz usul@SERVER_IP:/home/usul/
```

**2. Ship the database** (big — optionally gzip first to roughly halve it):
```bash
cd eshia-research
gzip -k -c eshia_research.db > eshia_research.db.gz     # optional, ~1–1.3 GB
scp eshia_research.db.gz usul@SERVER_IP:/home/usul/     # this takes a while; keep the window open
```
(If you skip gzip, just `scp eshia_research.db ...` — same target.)

**3. Unpack on the server** (`ssh usul@SERVER_IP`):
```bash
mkdir -p ~/usul16 && tar xzf ~/usul16-code.tgz -C ~/usul16
gunzip -c ~/eshia_research.db.gz > ~/usul16/eshia-research/eshia_research.db   # or: mv the .db in
rm ~/usul16-code.tgz ~/eshia_research.db.gz
ls -lh ~/usul16/eshia-research/eshia_research.db     # should show ~2.4G
```

---

## Part D — Backend (FastAPI)

```bash
cd ~/usul16/eshia-research
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e .            # installs the package + deps from pyproject.toml
.venv/bin/pip install "uvicorn[standard]"

# quick smoke test (Ctrl-C after you see it start):
PYTHONPATH=src DATABASE_URL="sqlite:////home/usul/usul16/eshia-research/eshia_research.db" \
  .venv/bin/uvicorn eshia_research.api.main:app --host 127.0.0.1 --port 8000
```
In another SSH window: `curl -s localhost:8000/health` → `{"status":"ok"}`. Then stop it.

**Make it a service** — `sudo nano /etc/systemd/system/usul16-api.service`:
```ini
[Unit]
Description=usul16 FastAPI backend
After=network.target

[Service]
User=usul
WorkingDirectory=/home/usul/usul16/eshia-research
Environment=PYTHONPATH=/home/usul/usul16/eshia-research/src
Environment=DATABASE_URL=sqlite:////home/usul/usul16/eshia-research/eshia_research.db
Environment=API_ALLOWED_ORIGINS=https://usul16.com,https://www.usul16.com
ExecStart=/home/usul/usul16/eshia-research/.venv/bin/uvicorn eshia_research.api.main:app --host 127.0.0.1 --port 8000 --workers 1 --timeout-keep-alive 120
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload && sudo systemctl enable --now usul16-api
sudo systemctl status usul16-api        # should be active (running)
```
(First graph request is slow ~10 s while it builds its cache — normal. Keep `--workers 1`:
each worker holds its own cache, so more workers just waste RAM at this traffic.)

---

## Part E — Frontend (Next.js)

```bash
cd ~/usul16/web
# tell the browser where the API is (same domain, /api path — no CORS):
echo 'NEXT_PUBLIC_API_BASE_URL=https://usul16.com/api' > .env.production
npm ci
npm run build            # uses swap if needed; a couple of minutes
```

**Make it a service** — `sudo nano /etc/systemd/system/usul16-web.service`:
```ini
[Unit]
Description=usul16 Next.js frontend
After=network.target usul16-api.service

[Service]
User=usul
WorkingDirectory=/home/usul/usul16/web
Environment=NODE_ENV=production
Environment=PORT=3000
ExecStart=/usr/bin/npm run start
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload && sudo systemctl enable --now usul16-web
curl -sI localhost:3000 | head -1        # HTTP/1.1 200 OK
```

---

## Part F — Caddy (routing + HTTPS)

`sudo nano /etc/caddy/Caddyfile` — replace the whole file with:
```
www.usul16.com {
    redir https://usul16.com{uri}
}

usul16.com {
    encode gzip
    handle_path /api/* {
        reverse_proxy 127.0.0.1:8000
    }
    handle {
        reverse_proxy 127.0.0.1:3000
    }
}
```
```bash
sudo systemctl reload caddy
```
Caddy automatically fetches a free Let's Encrypt certificate for usul16.com (needs the DNS from
Part A to be live and ports 80/443 open — they are).

---

## Part G — Go live ✅

Open **https://usul16.com** in a browser. Check:
- the home page, a book, a hadith (English shows),
- **/graph** (the network loads; try "Trace a path"),
- **/search**.

If a page 502s: `sudo journalctl -u usul16-api -n 50` or `-u usul16-web -n 50` to see why.

---

## Part H — Updating later

**Code change** (from your PC): commit, then either push to a private GitHub repo and `git pull`
on the server, or re-run the Part C tarball step. Then on the server:
```bash
cd ~/usul16/web && npm ci && npm run build && sudo systemctl restart usul16-web
# if backend changed:
cd ~/usul16/eshia-research && .venv/bin/pip install -e . && sudo systemctl restart usul16-api
```

**New database snapshot** (when the research DB improves): `scp` the new `.db` up (as in Part C),
replace the file, then `sudo systemctl restart usul16-api`. Keep the old one until the new one is
verified.

---

## Notes / safety
- The public API is **read-only** (no admin token set) and **/docs is disabled** — nothing can be
  written through the site.
- Only ports 22/80/443 are open.
- Back up the DB by keeping a copy off the server (you already have local copies).
- If you ever outgrow one box: this design scales *up* (bigger server) trivially; scaling *out*
  (multiple backend processes) needs a shared cache — a good problem for later, not now.
```
