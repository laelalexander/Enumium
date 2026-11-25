#!/usr/bin/env bash
# Install or update Pyslate on an Ubuntu server that already hosts other sites.
#
#   sudo bash install.sh            # install or update
#
# What it does, and nothing else:
#   - code in /var/www/pyslate.com/app, data in /var/www/pyslate.com/data
#   - a Python virtualenv (no Docker, no separate database: SQLite keeps memory low)
#   - a systemd service "pyslate" on 127.0.0.1:8100, capped at 512 MB of RAM
#   - an nginx site for pyslate.com (other sites are not touched), checked with nginx -t
#   - a free Let's Encrypt certificate once pyslate.com points at this server
set -euo pipefail

DOMAIN="${DOMAIN:-pyslate.com}"
REPO="${REPO:-https://github.com/laelalexander/enumium.git}"
ROOT="/var/www/${DOMAIN}"
# Use BRANCH if given; otherwise stay on the branch the server already runs, so a plain
# update never steps back to an older branch.
if [ -z "${BRANCH:-}" ] && [ -f "${ROOT}/branch" ]; then BRANCH="$(cat "${ROOT}/branch")"; fi
BRANCH="${BRANCH:-claude/pyslate-phase-1}"
PORT="${PORT:-8100}"
ENV_FILE="/etc/pyslate.env"

say()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
warn() { printf '\n\033[1;33m!!  %s\033[0m\n' "$*"; }
die()  { printf '\n\033[1;31mXX  %s\033[0m\n' "$*"; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Run as root (sudo bash install.sh)."

say "Checking the web server on port 80"
WEB=$(ss -ltnpH 'sport = :80' 2>/dev/null | grep -oE '"[a-z0-9_-]+"' | head -1 | tr -d '"' || true)
case "$WEB" in
  nginx|"") ;;
  *) die "Port 80 is served by '$WEB', not nginx. Stop here and send this message to Claude; the setup needs to match your existing server." ;;
esac

if ss -ltnH "sport = :${PORT}" | grep -q . && ! systemctl is-active --quiet pyslate; then
  die "Port ${PORT} is already in use by another program. Re-run with PORT=8110 (or another free port)."
fi

say "Installing system packages (git, Python, nginx, certbot)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git python3-venv python3-pip nginx certbot python3-certbot-nginx dnsutils >/dev/null

say "Creating ${ROOT}"
id pyslate >/dev/null 2>&1 || useradd --system --home "${ROOT}" --shell /usr/sbin/nologin pyslate
mkdir -p "${ROOT}/data"

if [ -d "${ROOT}/repo/.git" ]; then
  say "Updating the code (branch ${BRANCH})"
  git -C "${ROOT}/repo" fetch --depth 1 origin "${BRANCH}"
  git -C "${ROOT}/repo" checkout -q -B "${BRANCH}" FETCH_HEAD
else
  say "Downloading the code (branch ${BRANCH})"
  git clone -q --depth 1 --branch "${BRANCH}" "${REPO}" "${ROOT}/repo"
fi
ln -sfn "${ROOT}/repo/pyslate" "${ROOT}/app"
echo "${BRANCH}" > "${ROOT}/branch"

say "Installing Python dependencies (takes a few minutes the first time)"
[ -d "${ROOT}/venv" ] || python3 -m venv "${ROOT}/venv"
"${ROOT}/venv/bin/pip" install -q --upgrade pip
"${ROOT}/venv/bin/pip" install -q "${ROOT}/app"

NEW_PASSWORD=""
if [ ! -f "${ENV_FILE}" ]; then
  say "Creating settings in ${ENV_FILE}"
  NEW_PASSWORD=$(openssl rand -base64 18 | tr -d '/+=' | cut -c1-20)
  cat > "${ENV_FILE}" <<EOF
PYSLATE_PUBLIC_URL=https://${DOMAIN}
PYSLATE_DATA_DIR=${ROOT}/data
PYSLATE_ADMIN_TOKEN=${NEW_PASSWORD}
PYSLATE_SECRET_KEY=$(openssl rand -hex 32)
PYSLATE_MAX_UPLOAD_MB=50
# Add these for card payments:
# STRIPE_SECRET_KEY=
# STRIPE_WEBHOOK_SECRET=
EOF
  chmod 600 "${ENV_FILE}"
fi
if ! grep -q '^PYSLATE_AGENT_TOKEN=' "${ENV_FILE}"; then
  say "Adding a token for the shop agent (shown in the shop console under Shop agent)"
  printf '# The shop agent on the shop PC sends this to pick up machine jobs.\nPYSLATE_AGENT_TOKEN=%s\n' \
    "$(openssl rand -hex 24)" >> "${ENV_FILE}"
fi
chown -R pyslate:pyslate "${ROOT}/data"

say "Installing the pyslate service"
cat > /etc/systemd/system/pyslate.service <<EOF
[Unit]
Description=Pyslate (${DOMAIN})
After=network.target

[Service]
User=pyslate
Group=pyslate
EnvironmentFile=${ENV_FILE}
WorkingDirectory=${ROOT}/data
ExecStart=${ROOT}/venv/bin/uvicorn pyslate.app:create_app --factory --host 127.0.0.1 --port ${PORT} --workers 1 --proxy-headers
Restart=on-failure
MemoryMax=512M
NoNewPrivileges=true
ProtectSystem=full
ReadWritePaths=${ROOT}/data

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable -q pyslate
systemctl restart pyslate

say "Waiting for Pyslate to start"
for _ in $(seq 1 30); do
  curl -fs "http://127.0.0.1:${PORT}/api/health" >/dev/null && break
  sleep 1
done
curl -fs "http://127.0.0.1:${PORT}/api/health" >/dev/null || { journalctl -u pyslate -n 40 --no-pager; die "Pyslate did not start. Send the lines above to Claude."; }

say "Adding the nginx site for ${DOMAIN}"
SITE=/etc/nginx/sites-available/${DOMAIN}
if [ ! -f "${SITE}" ] || ! grep -q "managed-by-certbot\|ssl_certificate" "${SITE}"; then
  sed -e "s/server_name pyslate.com www.pyslate.com;/server_name ${DOMAIN} www.${DOMAIN};/" \
      -e "s#127.0.0.1:8100#127.0.0.1:${PORT}#" \
      "${ROOT}/app/deploy/nginx-pyslate.conf" > "${SITE}"
fi
ln -sfn "${SITE}" "/etc/nginx/sites-enabled/${DOMAIN}"
nginx -t || { rm -f "/etc/nginx/sites-enabled/${DOMAIN}"; die "nginx rejected the new site, so it was switched off again. Your other sites are unchanged."; }
systemctl reload nginx

say "Checking that ${DOMAIN} points at this server"
SERVER_IP=$(hostname -I | awk '{print $1}')
DNS_IP=$(dig +short A "${DOMAIN}" @1.1.1.1 | tail -1)
if [ "${DNS_IP}" != "${SERVER_IP}" ]; then
  warn "${DOMAIN} points to '${DNS_IP:-nothing}', but this server is ${SERVER_IP}."
  warn "At your domain registrar, set A records for ${DOMAIN} and www.${DOMAIN} to ${SERVER_IP}, wait a few minutes, then run this script again to get the SSL certificate."
else
  say "Getting the SSL certificate"
  WWW_ARGS=()
  [ "$(dig +short A "www.${DOMAIN}" @1.1.1.1 | tail -1)" = "${SERVER_IP}" ] && WWW_ARGS=(-d "www.${DOMAIN}")
  certbot --nginx -d "${DOMAIN}" "${WWW_ARGS[@]}" --redirect --non-interactive --agree-tos \
    --register-unsafely-without-email || warn "certbot failed; the site still works over http. Send the output above to Claude."
fi

say "Done"
echo "  Site:          https://${DOMAIN}"
echo "  Shop console:  https://${DOMAIN}/admin"
echo "  Production:    https://${DOMAIN}/admin/production"
if [ -n "${NEW_PASSWORD}" ]; then
  echo "  Admin password: ${NEW_PASSWORD}"
  echo "  (Saved in ${ENV_FILE}. Write it down; it is not shown again.)"
fi
echo "  Logs:          journalctl -u pyslate -f"
echo "  Update later:  sudo bash ${ROOT}/app/deploy/install.sh"
