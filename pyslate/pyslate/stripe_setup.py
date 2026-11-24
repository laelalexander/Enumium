"""Switch on Stripe card payments on the server.

Run on the Droplet as root:

    /var/www/pyslate.com/venv/bin/python -m pyslate.stripe_setup

It asks for your Stripe secret key (nothing is shown as you paste), checks it with
Stripe, creates the webhook that tells Pyslate when an order is paid, turns on the
customer portal for saved cards, saves both keys in /etc/pyslate.env and restarts
Pyslate. Keys are never printed.
"""

from __future__ import annotations

import getpass
import os
import re
import subprocess
import sys
from pathlib import Path

ENV_FILE = Path(os.environ.get("PYSLATE_ENV_FILE", "/etc/pyslate.env"))
EVENTS = ["checkout.session.completed", "checkout.session.async_payment_succeeded"]


def read_env(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    return out


def write_env(path: Path, values: dict[str, str]) -> None:
    """Set keys in the env file, replacing old or commented-out lines, keeping everything else."""
    lines = path.read_text().splitlines()
    done = set()
    for i, line in enumerate(lines):
        m = re.match(r"\s*#?\s*([A-Z_]+)\s*=", line)
        if m and m.group(1) in values and m.group(1) not in done:
            lines[i] = f"{m.group(1)}={values[m.group(1)]}"
            done.add(m.group(1))
    lines += [f"{k}={v}" for k, v in values.items() if k not in done]
    tmp = path.with_suffix(".tmp")
    tmp.write_text("\n".join(lines) + "\n")
    os.chmod(tmp, 0o600)
    tmp.replace(path)


def ask(prompt: str, default: str = "") -> str:
    got = input(prompt).strip()
    return got or default


def main() -> int:
    import stripe

    if not ENV_FILE.exists():
        print(f"{ENV_FILE} not found. Run the Pyslate installer first.")
        return 1
    env = read_env(ENV_FILE)
    public_url = env.get("PYSLATE_PUBLIC_URL", "https://pyslate.com").rstrip("/")
    hook_url = f"{public_url}/stripe/webhook"

    print("Stripe setup for", public_url)
    print("Find your secret key at https://dashboard.stripe.com/apikeys (use a test key, sk_test_..., to try it first).")
    key = getpass.getpass("Paste your Stripe secret key (hidden): ").strip()
    if not re.match(r"^(sk|rk)_(test|live)_[A-Za-z0-9]+$", key):
        print("That doesn't look like a Stripe secret key. It starts with sk_test_ or sk_live_.")
        return 1
    stripe.api_key = key
    mode = "TEST" if "_test_" in key else "LIVE"
    try:
        acct = stripe.Account.retrieve()
    except stripe.StripeError as exc:
        print("Stripe refused that key:", exc.user_message or str(exc))
        return 1
    name = (acct.get("settings") or {}).get("dashboard", {}).get("display_name") or acct.get("id")
    print(f"Key works: {name}, {mode} mode.")
    if mode == "LIVE" and not acct.get("charges_enabled"):
        print("Note: Stripe hasn't enabled live charges on this account yet. Finish activation in the Stripe dashboard.")

    # The webhook. Stripe only shows a signing secret when the endpoint is created.
    existing = [w for w in stripe.WebhookEndpoint.list(limit=100).auto_paging_iter() if w.get("url") == hook_url]
    if existing:
        print(f"A webhook for {hook_url} already exists in Stripe ({mode} mode).")
        if ask("Replace it with a new one so Pyslate gets its signing secret? [Y/n] ", "y").lower().startswith("n"):
            secret = getpass.getpass("Then paste that webhook's signing secret (whsec_..., hidden): ").strip()
            if not secret.startswith("whsec_"):
                print("That isn't a webhook signing secret.")
                return 1
        else:
            for w in existing:
                stripe.WebhookEndpoint.delete(w["id"])
            existing = []
    if not existing:
        hook = stripe.WebhookEndpoint.create(url=hook_url, enabled_events=EVENTS,
                                             description="Pyslate: marks orders paid")
        secret = hook["secret"]
        print(f"Created the webhook {hook_url}.")

    # The customer portal, where signed-in customers manage saved cards.
    try:
        if not list(stripe.billing_portal.Configuration.list(limit=1, is_default=True).auto_paging_iter()):
            stripe.billing_portal.Configuration.create(
                features={"payment_method_update": {"enabled": True}, "invoice_history": {"enabled": True}},
                default_return_url=f"{public_url}/account/settings",
            )
            print("Turned on the customer portal for saved cards.")
        else:
            print("The customer portal is already on.")
    except stripe.StripeError as exc:
        print("Couldn't turn on the customer portal:", exc.user_message or str(exc))
        print("Turn it on at https://dashboard.stripe.com/settings/billing/portal. Payments still work without it.")

    write_env(ENV_FILE, {"STRIPE_SECRET_KEY": key, "STRIPE_WEBHOOK_SECRET": secret})
    print(f"Saved both keys in {ENV_FILE}.")
    if subprocess.run(["systemctl", "restart", "pyslate"]).returncode == 0:
        print(f"Restarted Pyslate. Card payments are on ({mode} mode).")
    else:
        print("Saved, but couldn't restart. Run: systemctl restart pyslate")
    if mode == "TEST":
        print("Try an order with card 4242 4242 4242 4242, any future date and any CVC.")
        print("When it works, run this again with your live key (sk_live_...).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
