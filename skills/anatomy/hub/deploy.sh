#!/usr/bin/env bash
# Install or update the Anatomy Hub on an Ubuntu server that already runs nginx + certbot.
# Usage (as root, from this folder):  HUB_HOST=pyrails.com ./deploy.sh
# - Never restarts nginx: it writes one new site file, runs `nginx -t`, and only then reloads.
# - Leaves every other site alone. Prints the access key once on first install.
set -euo pipefail
HUB_HOST="${HUB_HOST:?set HUB_HOST, e.g. pyrails.com}"
SRC="$(cd "$(dirname "$0")" && pwd)"

command -v node >/dev/null || { echo "node is not installed"; exit 1; }
node -e 'process.exit(+process.versions.node.split(".")[0] >= 18 ? 0 : 1)' || { echo "node 18+ needed"; exit 1; }

id anatomy-hub >/dev/null 2>&1 || useradd --system --home /var/lib/anatomy-hub --shell /usr/sbin/nologin anatomy-hub
install -d -o anatomy-hub -g anatomy-hub -m 750 /var/lib/anatomy-hub
install -d -m 755 /opt/anatomy-hub
install -m 644 "$SRC/hub.js" /opt/anatomy-hub/hub.js
if [ ! -f /etc/anatomy-hub.env ]; then
  umask 077
  printf 'HUB_TOKEN=%s\nHUB_DATA=/var/lib/anatomy-hub\nHUB_PORT=4380\n' "$(openssl rand -hex 24)" > /etc/anatomy-hub.env
  chown root:anatomy-hub /etc/anatomy-hub.env; chmod 640 /etc/anatomy-hub.env
  NEW_KEY=1
fi
install -m 644 "$SRC/anatomy-hub.service" /etc/systemd/system/anatomy-hub.service
systemctl daemon-reload
systemctl enable anatomy-hub >/dev/null
systemctl restart anatomy-hub
sleep 1
curl -fsS http://127.0.0.1:4380/api/health

# nginx: the location block lives in a snippet; the site file for HUB_HOST includes it.
install -m 644 "$SRC/nginx-anatomy-hub.conf" /etc/nginx/snippets/anatomy-hub.conf
SITE=/etc/nginx/sites-available/anatomy-hub-$HUB_HOST
if ! grep -rqs "server_name[^;]*\b$HUB_HOST\b" /etc/nginx/sites-enabled/ || [ -f "$SITE" ]; then
  if [ ! -f "$SITE" ]; then
    cat > "$SITE" <<NGX
server {
    listen 80;
    listen [::]:80;
    server_name $HUB_HOST;
    include snippets/anatomy-hub.conf;
    location / { return 404; }
}
NGX
    ln -sf "$SITE" /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
    certbot --nginx -d "$HUB_HOST" --non-interactive --redirect --keep-until-expiring
  fi
else
  echo "A site for $HUB_HOST already exists. Add 'include snippets/anatomy-hub.conf;' to its HTTPS server block by hand."
fi
nginx -t && systemctl reload nginx
curl -fsS "https://$HUB_HOST/anatomy-hub/api/health" && echo
echo "Hub address: https://$HUB_HOST/anatomy-hub"
[ -n "${NEW_KEY:-}" ] && echo "Access key (enter it once in each PC's Anatomy > Hub): $(grep HUB_TOKEN /etc/anatomy-hub.env | cut -d= -f2)"
df -h /var/lib/anatomy-hub | tail -1
