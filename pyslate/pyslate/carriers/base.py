"""What every carrier connection shares: addresses, parcels, rates, labels, and HTTP.

Pyslate talks to UPS, FedEx and USPS directly with the shop's own carrier accounts. No
aggregator sits in between. Credentials live in the server's environment
(/etc/pyslate.env), never in the database or the code.
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

G_PER_LB = 453.59237
MM_PER_IN = 25.4


class CarrierError(RuntimeError):
    """A carrier refused or failed a request. The message is safe to show the shop."""


class NotConfigured(CarrierError):
    pass


@dataclass
class Address:
    name: str
    street: list[str]
    city: str
    state: str
    postal: str
    country: str = "US"
    phone: str = ""
    company: str = ""
    email: str = ""

    @property
    def zip5(self) -> str:
        return self.postal.split("-")[0][:5]

    @property
    def zip4(self) -> str:
        parts = self.postal.split("-")
        return parts[1] if len(parts) > 1 else ""


@dataclass
class Parcel:
    weight_g: float
    length_mm: float = 0
    width_mm: float = 0
    height_mm: float = 0

    @property
    def weight_lb(self) -> float:
        return max(0.1, round(self.weight_g / G_PER_LB, 2))

    @property
    def weight_oz(self) -> float:
        return round(self.weight_g / G_PER_LB * 16, 1)

    def dims_in(self) -> tuple[float, float, float] | None:
        if not (self.length_mm and self.width_mm and self.height_mm):
            return None
        return tuple(max(1.0, round(v / MM_PER_IN, 1)) for v in (self.length_mm, self.width_mm, self.height_mm))


@dataclass
class Rate:
    carrier: str
    service: str  # the carrier's own service code
    name: str
    amount: float
    currency: str = "USD"
    days: int | None = None


@dataclass
class Label:
    carrier: str
    service: str
    tracking: str
    data: bytes
    fmt: str  # png, gif, pdf, zpl
    cost: float | None = None
    shipment_id: str = ""  # what the carrier needs to void it, when that isn't the tracking number
    extra: dict = field(default_factory=dict)


@dataclass
class TrackInfo:
    status: str  # in_transit, delivered, exception, label_created, unknown
    detail: str
    delivered: bool = False
    events: list[dict] = field(default_factory=list)


# ---- HTTP -------------------------------------------------------------------------------


class Http:
    """A tiny JSON-over-HTTPS client. Tests swap `send` for a fake."""

    def __init__(self, timeout: float = 30):
        self.timeout = timeout

    def send(self, method: str, url: str, headers: dict, body: bytes | None) -> tuple[int, dict, bytes]:
        req = urllib.request.Request(url, data=body, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.status, dict(resp.headers), resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers or {}), exc.read()
        except OSError as exc:
            raise CarrierError(f"Could not reach the carrier: {exc}") from exc

    def json(self, method: str, url: str, headers: dict | None = None, payload=None, form: dict | None = None,
             expect=(200, 201)) -> tuple[dict, dict]:
        headers = dict(headers or {})
        body = None
        if form is not None:
            body = urllib.parse.urlencode(form).encode()
            headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
        elif payload is not None:
            body = json.dumps(payload).encode()
            headers.setdefault("Content-Type", "application/json")
        headers.setdefault("Accept", "application/json")
        status, resp_headers, raw = self.send(method, url, headers, body)
        try:
            data = json.loads(raw or b"{}")
        except ValueError:
            data = {"_raw": raw[:2000].decode(errors="replace")}
        if status not in expect:
            raise CarrierError(f"{status}: {error_text(data)}")
        return data, resp_headers


def error_text(data) -> str:
    """Pull the human message out of the three carriers' error shapes."""
    if not isinstance(data, dict):
        return str(data)[:400]
    msgs = []
    for key in ("errors", "Errors"):
        for e in data.get(key) or []:
            if isinstance(e, dict):
                msgs.append(str(e.get("message") or e.get("Message") or e.get("detail") or e.get("code") or e))
    resp = data.get("response") or {}
    for e in resp.get("errors") or []:
        msgs.append(str(e.get("message") or e))
    if data.get("error"):
        err = data["error"]
        msgs.append(str(err.get("message") if isinstance(err, dict) else err))
        if isinstance(err, dict):
            for e in err.get("errors") or []:
                msgs.append(str(e.get("detail") or e.get("message") or e))
    if data.get("error_description"):
        msgs.append(str(data["error_description"]))
    return "; ".join(m for m in msgs if m)[:600] or json.dumps(data)[:400]


class TokenCache:
    """OAuth client-credentials tokens, reused until a minute before they expire."""

    def __init__(self):
        self._tokens: dict[str, tuple[str, float]] = {}

    def get(self, key: str, fetch) -> str:
        token, expires = self._tokens.get(key, ("", 0.0))
        if token and time.time() < expires - 60:
            return token
        token, ttl = fetch()
        self._tokens[key] = (token, time.time() + float(ttl or 1800))
        return token


TOKENS = TokenCache()


def env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def basic(user: str, password: str) -> str:
    return "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()


# ---- addresses -------------------------------------------------------------------------

STATES = set(
    "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK "
    "OR PA RI SC SD TN TX UT VT VA WA WV WI WY PR VI GU AS MP AA AE AP".split()
)
_LAST = re.compile(r"^(?P<city>[A-Za-z .'\-]+?)[,\s]+(?P<state>[A-Za-z]{2})\.?\s+(?P<zip>\d{5}(?:-\d{4})?)$")


def parse_us_address(name: str, text: str, phone: str = "", email: str = "") -> Address:
    """Turn the free-text address from checkout into carrier fields.

    Expects the last line to read "City, ST 12345" (a trailing "USA" line is ignored)."""
    lines = [ln.strip() for ln in (text or "").replace("\r", "").split("\n") if ln.strip()]
    if lines and lines[-1].upper().rstrip(".") in ("USA", "US", "UNITED STATES", "UNITED STATES OF AMERICA"):
        lines = lines[:-1]
    if len(lines) == 1 and "," in lines[0]:  # "12 Bayou Rd, Apt 2, New Orleans, LA 70116"
        parts = [x.strip() for x in lines[0].split(",")]
        for k in (2, 1):
            tail = ", ".join(parts[-k:])
            if len(parts) > k and _LAST.match(tail):
                lines = parts[:-k] + [tail]
                break
    if len(lines) < 2:
        raise CarrierError("The address needs a street line and a 'City, ST ZIP' line")
    m = _LAST.match(lines[-1])
    if not m or m["state"].upper() not in STATES:
        raise CarrierError(f"Couldn't read city, state and ZIP from “{lines[-1]}”. Fix it in the form below.")
    street = lines[:-1]
    company = ""
    if len(street) > 2:
        company, street = street[0], street[1:]
    if street and street[0].strip().lower() == (name or "").strip().lower():
        street = street[1:]
    if not street:
        raise CarrierError("The address has no street line")
    return Address(name=name.strip(), street=street[:3], city=m["city"].strip().title() if m["city"].isupper() else m["city"].strip(),
                   state=m["state"].upper(), postal=m["zip"], phone=phone, company=company, email=email)
