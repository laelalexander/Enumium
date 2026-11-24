"""USPS, direct: the USPS APIs (apis.usps.com) with the shop's own USPS business account.

Postage is paid from the shop's USPS Enterprise Payment System (EPS) account, so the label
needs a payment authorization as well as the sign-in token.

Environment (/etc/pyslate.env):
  USPS_CLIENT_ID, USPS_CLIENT_SECRET   consumer key and secret from developers.usps.com
  USPS_CRID, USPS_MID                  Customer Registration ID and Mailer ID (Business Customer Gateway)
  USPS_MANIFEST_MID                    manifest Mailer ID (often the same as USPS_MID)
  USPS_EPS_ACCOUNT                     EPS account number that pays for postage
  USPS_ENV=test                        use apis-tem.usps.com until labels look right
"""

from __future__ import annotations

import json
from datetime import date
from email.parser import BytesParser
from email.policy import default as email_policy

from .base import Address, CarrierError, Http, Label, NotConfigured, Parcel, Rate, TOKENS, TrackInfo, env, error_text

SERVICES = {
    "USPS_GROUND_ADVANTAGE": "USPS Ground Advantage",
    "PRIORITY_MAIL": "USPS Priority Mail",
    "PRIORITY_MAIL_EXPRESS": "USPS Priority Mail Express",
}


class USPS:
    code, name = "usps", "USPS"

    def __init__(self, http: Http):
        self.http = http

    def configured(self) -> bool:
        return all(env(k) for k in ("USPS_CLIENT_ID", "USPS_CLIENT_SECRET", "USPS_CRID", "USPS_MID", "USPS_EPS_ACCOUNT"))

    @property
    def host(self) -> str:
        return "https://apis-tem.usps.com" if env("USPS_ENV", "production") == "test" else "https://apis.usps.com"

    def _token(self) -> str:
        if not self.configured():
            raise NotConfigured("USPS isn't connected")

        def fetch():
            data, _ = self.http.json("POST", f"{self.host}/oauth2/v3/token", payload={
                "client_id": env("USPS_CLIENT_ID"), "client_secret": env("USPS_CLIENT_SECRET"),
                "grant_type": "client_credentials"})
            if not data.get("access_token"):
                raise CarrierError("USPS sign-in failed")
            return data["access_token"], data.get("expires_in", 28000)

        return TOKENS.get(f"usps:{self.host}", fetch)

    def _payment_token(self) -> str:
        def fetch():
            role = {"CRID": env("USPS_CRID"), "MID": env("USPS_MID"),
                    "manifestMID": env("USPS_MANIFEST_MID") or env("USPS_MID"),
                    "accountType": "EPS", "accountNumber": env("USPS_EPS_ACCOUNT")}
            data, _ = self.http.json("POST", f"{self.host}/payments/v3/payment-authorization",
                                     {"Authorization": f"Bearer {self._token()}"},
                                     {"roles": [{"roleName": "PAYER", **role}, {"roleName": "LABEL_OWNER", **role}]})
            if not data.get("paymentAuthorizationToken"):
                raise CarrierError("USPS didn't authorize payment from the EPS account")
            return data["paymentAuthorizationToken"], 7 * 3600

        return TOKENS.get(f"usps-pay:{self.host}", fetch)

    def check(self) -> str:
        self._token()
        self._payment_token()
        return f"Signed in to USPS and EPS payment authorized ({'test' if 'tem' in self.host else 'production'})"

    @staticmethod
    def _address(a: Address) -> dict:
        first, _, last = a.name.partition(" ")
        out = {"firstName": first[:50], "lastName": (last or first)[:50], "streetAddress": a.street[0],
               "city": a.city, "state": a.state, "ZIPCode": a.zip5}
        if len(a.street) > 1:
            out["secondaryAddress"] = " ".join(a.street[1:])
        if a.zip4:
            out["ZIPPlus4"] = a.zip4
        if a.company:
            out["firm"] = a.company[:50]
        if a.phone:
            out["phone"] = "".join(ch for ch in a.phone if ch.isdigit())[:10]
        return out

    @staticmethod
    def _package(p: Parcel, mail_class: str) -> dict:
        dims = p.dims_in() or (6.0, 4.0, 2.0)
        return {"mailClass": mail_class, "rateIndicator": "SP", "weightUOM": "lb", "weight": p.weight_lb,
                "dimensionsUOM": "in", "length": dims[0], "width": dims[1], "height": dims[2],
                "processingCategory": "MACHINABLE", "mailingDate": date.today().isoformat(),
                "destinationEntryFacilityType": "NONE"}

    def rates(self, ship_from: Address, ship_to: Address, parcels: list[Parcel]) -> list[Rate]:
        headers = {"Authorization": f"Bearer {self._token()}"}
        out = []
        for mail_class, label in SERVICES.items():
            total = 0.0
            for p in parcels:
                pkg = self._package(p, mail_class)
                body = {"originZIPCode": ship_from.zip5, "destinationZIPCode": ship_to.zip5,
                        "weight": pkg["weight"], "length": pkg["length"], "width": pkg["width"], "height": pkg["height"],
                        "mailClass": mail_class, "processingCategory": "MACHINABLE", "rateIndicator": "SP",
                        "destinationEntryFacilityType": "NONE", "priceType": "COMMERCIAL",
                        "mailingDate": pkg["mailingDate"]}
                data, _ = self.http.json("POST", f"{self.host}/prices/v3/base-rates/search", headers, body)
                price = data.get("totalBasePrice")
                if price is None:
                    price = sum(float(r.get("price", 0)) for r in data.get("rates") or [])
                total += float(price or 0)
            out.append(Rate("usps", mail_class, label, round(total, 2)))
        return out

    def buy(self, ship_from: Address, ship_to: Address, parcels: list[Parcel], service: str,
            reference: str = "") -> list[Label]:
        fmt = env("USPS_LABEL_FORMAT", "PDF").upper()  # PDF, PNG or ZPL203DPI
        headers = {"Authorization": f"Bearer {self._token()}", "X-Payment-Authorization-Token": self._payment_token(),
                   "Content-Type": "application/json", "Accept": "application/vnd.usps.labels+json"}
        labels = []
        for p in parcels:
            body = {
                "imageInfo": {"imageType": fmt, "labelType": "4X6LABEL", "receiptOption": "NONE",
                              "suppressPostage": False, "suppressMailDate": False, "returnLabel": False},
                "toAddress": self._address(ship_to), "fromAddress": self._address(ship_from),
                "packageDescription": {**self._package(p, service), "extraServices": [],
                                       **({"customerReference": [{"referenceNumber": reference[:30]}]} if reference else {})},
            }
            status, resp_headers, raw = self.http.send("POST", f"{self.host}/labels/v3/label", headers,
                                                       json.dumps(body).encode())
            if status not in (200, 201):
                try:
                    detail = error_text(json.loads(raw or b"{}"))
                except ValueError:
                    detail = raw[:300].decode(errors="replace")
                raise CarrierError(f"{status}: {detail}")
            meta, image = parse_label_response(resp_headers, raw)
            if not image or not meta.get("trackingNumber"):
                raise CarrierError("USPS returned no label")
            ext = {"PDF": "pdf", "PNG": "png"}.get(fmt, "zpl")
            labels.append(Label("usps", service, meta["trackingNumber"], image, ext,
                                cost=float(meta["postage"]) if meta.get("postage") is not None else None))
        return labels

    def void(self, tracking: str, shipment_id: str = "") -> None:
        self.http.json("DELETE", f"{self.host}/labels/v3/label/{tracking}",
                       {"Authorization": f"Bearer {self._token()}",
                        "X-Payment-Authorization-Token": self._payment_token()}, expect=(200, 204))

    def track(self, tracking: str) -> TrackInfo:
        data, _ = self.http.json("GET", f"{self.host}/tracking/v3/tracking/{tracking}?expand=DETAIL",
                                 {"Authorization": f"Bearer {self._token()}"})
        desc = data.get("statusSummary") or data.get("status") or "No updates yet"
        category = (data.get("statusCategory") or "").lower()
        delivered = category == "delivered" or str(data.get("status", "")).lower().startswith("delivered")
        events = [{"at": e.get("eventTimestamp", ""), "text": e.get("eventType", ""), "where": e.get("eventCity", "")}
                  for e in (data.get("trackingEvents") or [])[:10]]
        return TrackInfo("delivered" if delivered else "in_transit", desc, delivered, events)


def parse_label_response(headers: dict, raw: bytes) -> tuple[dict, bytes]:
    """USPS answers with multipart/form-data: a labelMetadata JSON part and a labelImage part.
    Some setups return JSON with a base64 labelImage instead; both are handled."""
    ctype = next((v for k, v in headers.items() if k.lower() == "content-type"), "")
    if "multipart" in ctype.lower():
        msg = BytesParser(policy=email_policy).parsebytes(f"Content-Type: {ctype}\r\n\r\n".encode() + raw)
        meta, image = {}, b""
        for part in msg.iter_parts():
            name = part.get_param("name", header="content-disposition") or ""
            payload = part.get_payload(decode=True) or b""
            if name == "labelMetadata" or part.get_content_type() == "application/json":
                meta = json.loads(payload or b"{}")
            elif name == "labelImage" or not image:
                image = payload
        return meta, image
    import base64

    data = json.loads(raw or b"{}")
    meta = data.get("labelMetadata") or data
    img = data.get("labelImage") or ""
    return meta, base64.b64decode(img) if img else b""
