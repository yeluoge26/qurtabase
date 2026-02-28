#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# Qurtabase Production Deployment Script
# Target: 207.148.119.81  |  Domain: shijiebeitouzhu.com
# ═══════════════════════════════════════════════════════════════

SERVER="207.148.119.81"
USER="root"
DOMAIN="shijiebeitouzhu.com"
APP_DIR="/opt/qurtabase"
REPO="https://github.com/yeluoge26/qurtabase.git"
LOCAL_PROJECT="$(cd "$(dirname "$0")" && pwd)"

SSH_OPTS="-o StrictHostKeyChecking=no -o ControlMaster=auto -o ControlPath=/tmp/qb-ssh-%r@%h -o ControlPersist=300"

# ── Colors ──
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
step() { echo -e "\n${CYAN}[$(date +%H:%M:%S)]${NC} ${GREEN}▸ $1${NC}"; }
warn() { echo -e "${YELLOW}  ⚠ $1${NC}"; }
err()  { echo -e "${RED}  ✗ $1${NC}"; exit 1; }

# ── Pre-flight checks ──
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo -e "${CYAN}  Qurtabase Deployment → ${DOMAIN}${NC}"
echo -e "${CYAN}  Server: ${SERVER}${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"

# Check local files exist
[ -d "$LOCAL_PROJECT/backend" ]                     || err "backend/ not found"
[ -d "$LOCAL_PROJECT/frontend/dist" ]               || err "frontend/dist/ not found. Run: cd frontend && npm run build"
[ -f "$LOCAL_PROJECT/backend/models/trained/model_calibrated.pkl" ] || warn "No trained model found — will run in demo mode"

# ── Step 1: Establish SSH connection (password prompt here — only once) ──
step "Establishing SSH connection to ${SERVER}..."
ssh $SSH_OPTS ${USER}@${SERVER} "echo 'SSH connection OK'" || err "SSH failed"

# ── Step 2: Upload git-ignored files (models, dist, .env) ──
step "Uploading git-ignored files (models, frontend dist)..."

ssh $SSH_OPTS ${USER}@${SERVER} "mkdir -p ${APP_DIR}"

# Upload frontend dist
rsync -avz --delete -e "ssh $SSH_OPTS" \
  "$LOCAL_PROJECT/frontend/dist/" \
  ${USER}@${SERVER}:${APP_DIR}/frontend/dist/

# Upload trained models
if [ -d "$LOCAL_PROJECT/backend/models/trained" ]; then
  rsync -avz -e "ssh $SSH_OPTS" \
    "$LOCAL_PROJECT/backend/models/trained/" \
    ${USER}@${SERVER}:${APP_DIR}/backend/models/trained/
fi

# Upload .env — check both project root and backend/
step "Uploading .env..."
if [ -f "$LOCAL_PROJECT/.env" ]; then
  scp $SSH_OPTS "$LOCAL_PROJECT/.env" ${USER}@${SERVER}:${APP_DIR}/backend/.env
elif [ -f "$LOCAL_PROJECT/backend/.env" ]; then
  scp $SSH_OPTS "$LOCAL_PROJECT/backend/.env" ${USER}@${SERVER}:${APP_DIR}/backend/.env
else
  warn "No .env found — will create default on server"
fi

# Upload backtest/prediction JSON files
for f in backtest_results.json predictions_upcoming.json; do
  if [ -f "$LOCAL_PROJECT/backend/$f" ]; then
    scp $SSH_OPTS "$LOCAL_PROJECT/backend/$f" ${USER}@${SERVER}:${APP_DIR}/backend/$f
  fi
done

# Upload intl_elo_ratings.json
if [ -f "$LOCAL_PROJECT/backend/models/trained/intl_elo_ratings.json" ]; then
  scp $SSH_OPTS "$LOCAL_PROJECT/backend/models/trained/intl_elo_ratings.json" \
    ${USER}@${SERVER}:${APP_DIR}/backend/models/trained/intl_elo_ratings.json
fi

# ── Step 3: Run server-side setup ──
step "Running server-side setup..."

ssh $SSH_OPTS ${USER}@${SERVER} bash << 'REMOTE_SETUP'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

APP_DIR="/opt/qurtabase"
DOMAIN="shijiebeitouzhu.com"
REPO="https://github.com/yeluoge26/qurtabase.git"

echo ">>> [1/7] Installing system packages..."
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip python3-dev \
  nginx certbot python3-certbot-nginx \
  git curl redis-server build-essential > /dev/null 2>&1

# Start Redis
systemctl enable redis-server
systemctl start redis-server

echo ">>> [2/7] Cloning / updating repository..."
if [ -d "$APP_DIR/.git" ]; then
  cd "$APP_DIR"
  git fetch origin
  git reset --hard origin/main
else
  # Clone but preserve uploaded files
  TEMP_DIR=$(mktemp -d)
  [ -d "$APP_DIR/frontend/dist" ] && cp -r "$APP_DIR/frontend/dist" "$TEMP_DIR/dist"
  [ -d "$APP_DIR/backend/models/trained" ] && cp -r "$APP_DIR/backend/models/trained" "$TEMP_DIR/trained"
  [ -f "$APP_DIR/backend/.env" ] && cp "$APP_DIR/backend/.env" "$TEMP_DIR/.env"
  [ -f "$APP_DIR/backend/backtest_results.json" ] && cp "$APP_DIR/backend/backtest_results.json" "$TEMP_DIR/backtest_results.json"
  [ -f "$APP_DIR/backend/predictions_upcoming.json" ] && cp "$APP_DIR/backend/predictions_upcoming.json" "$TEMP_DIR/predictions_upcoming.json"

  rm -rf "$APP_DIR"
  git clone "$REPO" "$APP_DIR"
  cd "$APP_DIR"

  # Restore uploaded files
  [ -d "$TEMP_DIR/dist" ] && mkdir -p frontend && cp -r "$TEMP_DIR/dist" frontend/dist
  [ -d "$TEMP_DIR/trained" ] && mkdir -p backend/models && cp -r "$TEMP_DIR/trained" backend/models/trained
  [ -f "$TEMP_DIR/.env" ] && cp "$TEMP_DIR/.env" backend/.env
  [ -f "$TEMP_DIR/backtest_results.json" ] && cp "$TEMP_DIR/backtest_results.json" backend/backtest_results.json
  [ -f "$TEMP_DIR/predictions_upcoming.json" ] && cp "$TEMP_DIR/predictions_upcoming.json" backend/predictions_upcoming.json
  rm -rf "$TEMP_DIR"
fi

echo ">>> [3/7] Setting up Python virtual environment..."
cd "$APP_DIR/backend"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo ">>> [4/7] Configuring .env..."
if [ -f "$APP_DIR/backend/.env" ]; then
  # Fix Redis URL for non-Docker (redis://redis:6379 → redis://localhost:6379)
  sed -i 's|redis://redis:|redis://localhost:|g' "$APP_DIR/backend/.env"
  echo "  .env found — Redis URL fixed for bare-metal"
else
  cat > "$APP_DIR/backend/.env" << 'ENVEOF'
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
  echo "  ⚠ Created default .env — edit API keys: nano $APP_DIR/backend/.env"
fi

# Also copy .env to project root (load_dotenv searches parent dirs)
cp "$APP_DIR/backend/.env" "$APP_DIR/.env"

echo ">>> [5/7] Configuring systemd service..."
cat > /etc/systemd/system/qurtabase.service << SVCEOF
[Unit]
Description=Qurtabase AI Football Quant Terminal
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}/backend
Environment=PATH=${APP_DIR}/backend/venv/bin:/usr/local/bin:/usr/bin
ExecStart=${APP_DIR}/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
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

echo ">>> [6/7] Configuring Nginx..."
cat > /etc/nginx/sites-available/qurtabase << 'NGXEOF'
# Redirect www → apex
server {
    listen 80;
    server_name www.shijiebeitouzhu.com;
    return 301 https://shijiebeitouzhu.com$request_uri;
}

# Main site — frontend + backend + WebSocket
server {
    listen 80;
    server_name shijiebeitouzhu.com;

    client_max_body_size 10M;

    # WebSocket
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

    # Everything else → backend (API + static files)
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

    # WebSocket on API subdomain too
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
NGXEOF

# Enable site
ln -sf /etc/nginx/sites-available/qurtabase /etc/nginx/sites-enabled/qurtabase
rm -f /etc/nginx/sites-enabled/default

# Test and reload
nginx -t
systemctl enable nginx
systemctl restart nginx

echo ">>> [7/7] Setting up SSL (Let's Encrypt)..."
certbot --nginx --non-interactive --agree-tos \
  --email admin@shijiebeitouzhu.com \
  -d shijiebeitouzhu.com \
  -d www.shijiebeitouzhu.com \
  -d api.shijiebeitouzhu.com \
  --redirect || echo "  ⚠ SSL setup failed — you can retry manually: certbot --nginx -d shijiebeitouzhu.com -d www.shijiebeitouzhu.com -d api.shijiebeitouzhu.com"

# Set up auto-renewal
systemctl enable certbot.timer 2>/dev/null || true

echo ""
echo "══════════════════════════════════════════════"
echo "  ✓ Deployment complete!"
echo "  App:    https://shijiebeitouzhu.com"
echo "  API:    https://api.shijiebeitouzhu.com/api/health"
echo "  Admin:  https://shijiebeitouzhu.com/admin/"
echo "  Logs:   journalctl -u qurtabase -f"
echo "  .env:   ${APP_DIR}/backend/.env"
echo "══════════════════════════════════════════════"

REMOTE_SETUP

# ── Step 4: Verify deployment ──
step "Verifying deployment..."
sleep 3
ssh $SSH_OPTS ${USER}@${SERVER} "systemctl is-active qurtabase && curl -sf http://localhost:8000/api/health | python3 -c 'import sys,json;d=json.load(sys.stdin);print(\"Health:\",d[\"status\"],\"| Model:\",d[\"model_loaded\"],\"| Mode:\",\"LIVE\" if not d[\"demo_mode\"] else \"DEMO\")'"

# Close SSH control socket
ssh -O exit $SSH_OPTS ${USER}@${SERVER} 2>/dev/null || true

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Deployment successful!${NC}"
echo -e "${GREEN}  https://shijiebeitouzhu.com${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
