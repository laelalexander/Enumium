# Pyslate

Pyslate is the customer site for the shop at pyslate.com. A customer uploads a part, gets an instant price, and pays. The order then lands in the shop's production queue for the 3D printers or the xTool lasers.

This folder is **phase 1** of the plan: upload, quote, checkout and a manual production queue. The shop agent that sends jobs straight to the machines comes in phase 3.

## What phase 1 does

- **Landing page** with drag-and-drop upload (STL, 3MF, OBJ, PLY, DXF).
- **Part check.** Each file is measured for size, volume, flatness, sheet thickness and cut length, and problems are flagged (open meshes, features under 0.8 mm).
- **Routing**, using the shop rule: sort first, then route.
  - A flat part in a sheet material whose thickness matches goes to the **laser line**: xTool X1 or M2 for wood and acrylic, MetalFab for steel.
  - A 3D part goes to the **print line** (Bambu Lab).
  - Anything that doesn't fit a machine, or doesn't suit the chosen material, goes to **review** and can't be ordered until it's fixed.
- **Instant price** with a breakdown the customer can see: material, machine time, setup, quantity discount, rush, minimum order.
- **Interactive 3D preview** of meshes (three.js) and an outline preview of DXF drawings.
- **Checkout.** Payment goes through Stripe Checkout when `STRIPE_SECRET_KEY` is set. Without a key, the order waits for the shop to mark it paid.
- **Order tracking page** for the customer: Awaiting payment, In queue, Making, Finishing, Shipped, Delivered.
- **Shop console** at `/admin`:
  - a queue lane per machine, with Start, Done, Failed and Requeue buttons;
  - an order list and order detail with status, tracking and file downloads;
  - a rates and machines editor.

## Rates and machines

The starting values in `pyslate/shop.py` are placeholders. Edit them in **Admin > Rates and machines**:

- materials and thicknesses you stock;
- machine bed sizes (X1, M2 and MetalFab are marked "confirm bed size");
- hourly rates, setup fees, margin and quantity breaks.

Quotes use the saved values right away. A placed order keeps the price it was ordered at.

## Run locally

```bash
cd pyslate
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
PYSLATE_ADMIN_TOKEN=change-me uvicorn pyslate.app:create_app --factory --reload
# open http://localhost:8000 and http://localhost:8000/admin
pytest
```

Data (a SQLite database and the uploaded files) goes into `./data` unless `DATABASE_URL` and `PYSLATE_DATA_DIR` say otherwise.

## Deploy on the DigitalOcean Droplet

Pyslate runs next to Pyrails.com on the same Droplet. It listens only on `127.0.0.1:8100`, and the Droplet's web server proxies `pyslate.com` to it.

1. Point the `pyslate.com` DNS A record at the Droplet's IP.
2. Copy this folder to the Droplet, then `cp .env.example .env` and fill in the values.
3. `docker compose up -d --build`
4. Install `deploy/nginx-pyslate.conf` as an nginx site and run `certbot --nginx -d pyslate.com -d www.pyslate.com`. If Pyrails.com is served by something other than nginx, use the same proxy settings in that server.
5. For card payments, add a Stripe webhook to `https://pyslate.com/stripe/webhook` for the `checkout.session.completed` event, and put its signing secret in `STRIPE_WEBHOOK_SECRET`.

## Layout

| Path | What it is |
| --- | --- |
| `pyslate/geometry.py` | Reads meshes (trimesh) and DXF drawings (ezdxf); measures size, volume, flatness and cut length |
| `pyslate/routing.py` | Picks the laser line, the print line or review for each part |
| `pyslate/pricing.py` | Prices each line and the whole quote |
| `pyslate/shop.py` | Default machines, materials and rates, and validation of edits |
| `pyslate/services.py` | Quote, order and job operations |
| `pyslate/app.py` | Web routes: customer pages, admin console, Stripe webhook |
| `pyslate/models.py` | Database tables, plus order and job states |

## Next phases

- **Phase 2:** STEP upload, in-browser designer, DFM warnings highlighted on the model.
- **Phase 3:** a shop agent that pulls jobs and drives the machines:
  - xTool X1, M2 and MetalFab over the WebSocket API on port 28900;
  - Bambu Lab printers in LAN mode;
  - the custom printers through Nero on-prem.
- **Phase 4:** scheduling, sheet nesting, stock and shipping labels.
- **Phase 5:** the marketplace.
