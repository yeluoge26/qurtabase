#!/usr/bin/env python3
"""
Qurtabase Production Deployment Script
Target: 207.148.119.81 | Domain: shijiebeitouzhu.com
Uses paramiko for SSH (no sshpass needed)
"""

import paramiko
import os
import sys
import stat
import time

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SERVER   = "207.148.119.81"
USER     = "root"
PASSWORD = os.environ.get("DEPLOY_PASSWORD", r"rG3).fvyN}kWVD#C")
DOMAIN   = "shijiebeitouzhu.com"
APP_DIR  = "/opt/qurtabase"
REPO     = "https://github.com/yeluoge26/qurtabase.git"

LOCAL_PROJECT = os.path.dirname(os.path.abspath(__file__))

# ── Helpers ──────────────────────────────────────────────────

def step(msg):
    print(f"\n\033[0;36m[{time.strftime('%H:%M:%S')}]\033[0m \033[0;32m▸ {msg}\033[0m")

def warn(msg):
    print(f"  \033[1;33m⚠ {msg}\033[0m")

def err(msg):
    print(f"  \033[0;31m✗ {msg}\033[0m")
    sys.exit(1)

def ssh_exec(client, cmd, check=True):
    """Execute command on remote server and print output."""
    stdin, stdout, stderr = client.exec_command(cmd, timeout=300)
    out = stdout.read().decode()
    error = stderr.read().decode()
    exit_code = stdout.channel.recv_exit_status()
    if out.strip():
        print(out.strip())
    if error.strip() and exit_code != 0:
        print(error.strip())
    if check and exit_code != 0:
        warn(f"Command exited with code {exit_code}")
    return exit_code, out, error

def sftp_upload_dir(sftp, local_dir, remote_dir):
    """Recursively upload a directory."""
    try:
        sftp.stat(remote_dir)
    except FileNotFoundError:
        sftp.mkdir(remote_dir)

    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = f"{remote_dir}/{item}"

        if os.path.isfile(local_path):
            print(f"    ↑ {item}")
            sftp.put(local_path, remote_path)
        elif os.path.isdir(local_path):
            sftp_upload_dir(sftp, local_path, remote_path)

def sftp_mkdir_p(sftp, remote_dir):
    """mkdir -p equivalent over SFTP."""
    dirs_to_create = []
    d = remote_dir
    while d and d != "/":
        try:
            sftp.stat(d)
            break
        except FileNotFoundError:
            dirs_to_create.append(d)
            d = os.path.dirname(d)
    for d in reversed(dirs_to_create):
        sftp.mkdir(d)

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

print("\033[0;36m═══════════════════════════════════════════════\033[0m")
print(f"\033[0;36m  Qurtabase Deployment → {DOMAIN}\033[0m")
print(f"\033[0;36m  Server: {SERVER}\033[0m")
print("\033[0;36m═══════════════════════════════════════════════\033[0m")

# ── Step 1: Connect ──
step("Establishing SSH connection...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(SERVER, username=USER, password=PASSWORD, timeout=30)
except Exception as e:
    err(f"SSH connection failed: {e}")

print("  SSH connection OK")

# Set up SSH key for future passwordless access
step("Setting up SSH key for future access...")
local_pubkey = os.path.expanduser("~/.ssh/id_ed25519.pub")
if os.path.exists(local_pubkey):
    with open(local_pubkey) as f:
        pubkey = f.read().strip()
    ssh_exec(client, f'mkdir -p ~/.ssh && chmod 700 ~/.ssh && grep -qF "{pubkey}" ~/.ssh/authorized_keys 2>/dev/null || echo "{pubkey}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys')
    print("  SSH key installed")
else:
    warn("No local SSH key found — skipping key setup")

# ── Step 2: Upload files via SFTP ──
step("Uploading files via SFTP...")
sftp = client.open_sftp()

# Create directories
for d in [APP_DIR, f"{APP_DIR}/frontend", f"{APP_DIR}/backend",
          f"{APP_DIR}/backend/models", f"{APP_DIR}/backend/models/trained"]:
    sftp_mkdir_p(sftp, d)

# Upload frontend/dist
dist_dir = os.path.join(LOCAL_PROJECT, "frontend", "dist")
if os.path.isdir(dist_dir):
    print("  Uploading frontend/dist/...")
    sftp_mkdir_p(sftp, f"{APP_DIR}/frontend/dist")
    sftp_upload_dir(sftp, dist_dir, f"{APP_DIR}/frontend/dist")
else:
    warn("frontend/dist/ not found — frontend won't be served")

# Upload trained models
models_dir = os.path.join(LOCAL_PROJECT, "backend", "models", "trained")
if os.path.isdir(models_dir):
    print("  Uploading backend/models/trained/...")
    for f in os.listdir(models_dir):
        fpath = os.path.join(models_dir, f)
        if os.path.isfile(fpath):
            print(f"    ↑ {f}")
            sftp.put(fpath, f"{APP_DIR}/backend/models/trained/{f}")

# Upload .env
env_path = os.path.join(LOCAL_PROJECT, ".env")
if not os.path.exists(env_path):
    env_path = os.path.join(LOCAL_PROJECT, "backend", ".env")
if os.path.exists(env_path):
    print("  Uploading .env...")
    sftp.put(env_path, f"{APP_DIR}/backend/.env")

# Upload data JSON files
for f in ["backtest_results.json", "predictions_upcoming.json"]:
    fpath = os.path.join(LOCAL_PROJECT, "backend", f)
    if os.path.exists(fpath):
        print(f"  Uploading {f}...")
        sftp.put(fpath, f"{APP_DIR}/backend/{f}")

sftp.close()

# ── Step 3: Server setup ──
step("[1/7] Installing system packages...")
ssh_exec(client, """
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip python3-dev \
  nginx certbot python3-certbot-nginx \
  git curl redis-server build-essential 2>&1 | tail -3
systemctl enable redis-server
systemctl start redis-server
""")

step("[2/7] Cloning / updating repository...")
ssh_exec(client, f"""
if [ -d "{APP_DIR}/.git" ]; then
  cd {APP_DIR}
  git fetch origin
  git reset --hard origin/main
else
  TEMP_DIR=$(mktemp -d)
  # Save uploaded files
  [ -d "{APP_DIR}/frontend/dist" ] && cp -r {APP_DIR}/frontend/dist $TEMP_DIR/dist
  [ -d "{APP_DIR}/backend/models/trained" ] && cp -r {APP_DIR}/backend/models/trained $TEMP_DIR/trained
  [ -f "{APP_DIR}/backend/.env" ] && cp {APP_DIR}/backend/.env $TEMP_DIR/.env
  [ -f "{APP_DIR}/backend/backtest_results.json" ] && cp {APP_DIR}/backend/backtest_results.json $TEMP_DIR/backtest_results.json
  [ -f "{APP_DIR}/backend/predictions_upcoming.json" ] && cp {APP_DIR}/backend/predictions_upcoming.json $TEMP_DIR/predictions_upcoming.json

  rm -rf {APP_DIR}
  git clone {REPO} {APP_DIR}
  cd {APP_DIR}

  # Restore
  [ -d "$TEMP_DIR/dist" ] && mkdir -p frontend && cp -r $TEMP_DIR/dist frontend/dist
  [ -d "$TEMP_DIR/trained" ] && mkdir -p backend/models && cp -r $TEMP_DIR/trained backend/models/trained
  [ -f "$TEMP_DIR/.env" ] && cp $TEMP_DIR/.env backend/.env
  [ -f "$TEMP_DIR/backtest_results.json" ] && cp $TEMP_DIR/backtest_results.json backend/backtest_results.json
  [ -f "$TEMP_DIR/predictions_upcoming.json" ] && cp $TEMP_DIR/predictions_upcoming.json backend/predictions_upcoming.json
  rm -rf $TEMP_DIR
fi
echo "Git repo ready"
""")

step("[3/7] Setting up Python virtual environment...")
ssh_exec(client, f"""
cd {APP_DIR}/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "Python venv ready"
""")

step("[4/7] Configuring .env...")
ssh_exec(client, f"""
if [ -f "{APP_DIR}/backend/.env" ]; then
  # Fix Redis URL for non-Docker
  sed -i 's|redis://redis:|redis://localhost:|g' {APP_DIR}/backend/.env
  echo ".env found — Redis URL fixed for bare-metal"
else
  cat > {APP_DIR}/backend/.env << 'ENVEOF'
HOST=0.0.0.0
PORT=8000
ALLSPORTS_API_KEY=
SPORTMONKS_API_KEY=
FOOTBALL_API_KEY=
ODDS_API_KEY=
REDIS_URL=redis://localhost:6379
MODEL_PATH=models/trained/model_calibrated.pkl
MODEL_META_PATH=models/trained/model_meta.json
ENVEOF
  echo "Created default .env — edit keys: nano {APP_DIR}/backend/.env"
fi
cp {APP_DIR}/backend/.env {APP_DIR}/.env
""")

step("[5/7] Configuring systemd service...")
ssh_exec(client, f"""
cat > /etc/systemd/system/qurtabase.service << 'SVCEOF'
[Unit]
Description=Qurtabase AI Football Quant Terminal
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory={APP_DIR}/backend
Environment=PATH={APP_DIR}/backend/venv/bin:/usr/local/bin:/usr/bin
ExecStart={APP_DIR}/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable qurtabase
systemctl restart qurtabase
sleep 2
systemctl is-active qurtabase && echo "Service: RUNNING" || echo "Service: FAILED"
""")

step("[6/7] Configuring Nginx...")
nginx_conf = r"""
# Redirect www → apex
server {
    listen 80;
    server_name www.shijiebeitouzhu.com;
    return 301 https://shijiebeitouzhu.com$request_uri;
}

# Main site
server {
    listen 80;
    server_name shijiebeitouzhu.com;

    client_max_body_size 10M;

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# API subdomain
server {
    listen 80;
    server_name api.shijiebeitouzhu.com;

    client_max_body_size 10M;

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""
# Write nginx config via heredoc (avoid escaping issues)
ssh_exec(client, f"""
cat > /etc/nginx/sites-available/qurtabase << 'NGXEOF'
{nginx_conf}
NGXEOF

ln -sf /etc/nginx/sites-available/qurtabase /etc/nginx/sites-enabled/qurtabase
rm -f /etc/nginx/sites-enabled/default
nginx -t && echo "Nginx config OK" || echo "Nginx config FAILED"
systemctl enable nginx
systemctl restart nginx
""")

step("[7/7] Setting up SSL (Let's Encrypt)...")
exit_code, out, error = ssh_exec(client, f"""
certbot --nginx --non-interactive --agree-tos \
  --email admin@{DOMAIN} \
  -d {DOMAIN} \
  -d www.{DOMAIN} \
  -d api.{DOMAIN} \
  --redirect 2>&1
""", check=False)
if exit_code != 0:
    warn("SSL setup had issues — may need manual retry")
    warn(f"Run on server: certbot --nginx -d {DOMAIN} -d www.{DOMAIN} -d api.{DOMAIN}")

# Enable auto-renewal
ssh_exec(client, "systemctl enable certbot.timer 2>/dev/null || true", check=False)

# ── Step 4: Verify ──
step("Verifying deployment...")
time.sleep(3)
exit_code, out, _ = ssh_exec(client, """
systemctl is-active qurtabase
curl -sf http://localhost:8000/api/health | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('Health:', d['status'])
print('Model:', d['model_loaded'])
print('Mode:', 'LIVE' if not d['demo_mode'] else 'DEMO')
print('Active:', d['active_matches'])
"
""")

client.close()

print()
print("\033[0;32m═══════════════════════════════════════════════\033[0m")
print(f"\033[0;32m  Deployment complete!\033[0m")
print(f"\033[0;32m  App:   https://{DOMAIN}\033[0m")
print(f"\033[0;32m  API:   https://api.{DOMAIN}/api/health\033[0m")
print(f"\033[0;32m  Admin: https://{DOMAIN}/admin/\033[0m")
print(f"\033[0;32m  Logs:  ssh {USER}@{SERVER} journalctl -u qurtabase -f\033[0m")
print("\033[0;32m═══════════════════════════════════════════════\033[0m")
