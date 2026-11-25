"""UPS, direct: OAuth client credentials + the UPS REST APIs, with the shop's UPS account.

Environment (/etc/pyslate.env):
  UPS_CLIENT_ID, UPS_CLIENT_SECRET   from the app on developer.ups.com
  UPS_ACCOUNT                        6-character UPS shipper number (bills the postage)
  UPS_ENV=test                       use UPS's test host (wwwcie.ups.com) until labels look right
  UPS_API_VERSION=v2409              shipping/rating API version in the URL path
"""

from __future__ import annotations

import base64
import uuid
from datetime import date

from .base import Address, CarrierError, Http, Label, NotConfigured, Parcel, Rate, TOKENS, TrackInfo, basic, env

SERVICES = {
    "03": "UPS Ground", "12": "UPS 3 Day Select", "02": "UPS 2nd Day Air", "59": "UPS 2nd Day Air A.M.",
    "13": "UPS Next Day Air Saver", "01": "UPS Next Day Air", "14": "UPS Next Day Air Early",
}


def _list(v):
    return v if isinstance(v, list) else [v] if v else []


class UPS:
    code, name = "ups", "UPS"

    def __init__(self, http: Http):
        self.http = http

    def configured(self) -> bool:
        return bool(env("UPS_CLIENT_ID") and env("UPS_CLIENT_SECRET") and env("UPS_ACCOUNT"))

    @property
    def host(self) -> str:
        return "https://wwwcie.ups.com" if env("UPS_ENV", "production") == "test" else "https://onlinetools.ups.com"

    @property
    def version(self) -> str:
        return env("UPS_API_VERSION", "v2409")

    def _token(self) -> str:
        if not self.configured():
            raise NotConfigured("UPS isn't connected")

        def fetch():
            data, _ = self.http.json(
                "POST", f"{self.host}/security/v1/oauth/token", form={"grant_type": "client_credentials"},
                headers={"Authorization": basic(env("UPS_CLIENT_ID"), env("UPS_CLIENT_SECRET")),
                         "x-merchant-id": env("UPS_ACCOUNT")})
            if not data.get("access_token"):
                raise CarrierError("UPS sign-in failed")
            return data["access_token"], data.get("expires_in", 14399)

        return TOKENS.get(f"ups:{self.host}", fetch)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token()}", "transId": uuid.uuid4().hex[:32], "transactionSrc": "pyslate"}

    def check(self) -> str:
        self._token()
        return f"Signed in to UPS ({'test' if 'wwwcie' in self.host else 'production'})"

    # -- building blocks --

    @staticmethod
    def _addr(a: Address) -> dict:
        return {"AddressLine": a.street[:3], "City": a.city, "StateProvinceCode": a.state,
                "PostalCode": a.postal, "CountryCode": a.country}

    def _party(self, a: Address, shipper: bool = False) -> dict:
        out = {"Name": (a.company or a.name)[:35], "AttentionName": a.name[:35], "Address": self._addr(a)}
        if a.phone:
            out["Phone"] = {"Number": "".join(ch for ch in a.phone if ch.isdigit())[:15]}
        if shipper:
            out["ShipperNumber"] = env("UPS_ACCOUNT")
        return out

    @staticmethod
    def _packages(parcels: list[Parcel], key: str) -> list[dict]:
        out = []
        for p in parcels:
            pkg = {key: {"Code": "02", "Description": "Package"},
                   "PackageWeight": {"UnitOfMeasurement": {"Code": "LBS"}, "Weight": f"{p.weight_lb:.1f}"}}
            dims = p.dims_in()
            if dims:
                pkg["Dimensions"] = {"UnitOfMeasurement": {"Code": "IN"},
                                     "Length": f"{dims[0]:.0f}", "Width": f"{dims[1]:.0f}", "Height": f"{dims[2]:.0f}"}
            out.append(pkg)
        return out

    # -- the four things Pyslate needs --

    def rates(self, ship_from: Address, ship_to: Address, parcels: list[Parcel]) -> list[Rate]:
        body = {"RateRequest": {
            "Request": {"RequestOption": "Shop", "SubVersion": self.version.lstrip("v")},
            "Shipment": {
                "Shipper": self._party(ship_from, shipper=True), "ShipFrom": self._party(ship_from),
                "ShipTo": self._party(ship_to),
                "PaymentDetails": {"ShipmentCharge": [{"Type": "01", "BillShipper": {"AccountNumber": env("UPS_ACCOUNT")}}]},
                "ShipmentRatingOptions": {"NegotiatedRatesIndicator": "Y"},
                "NumOfPieces": str(len(parcels)),
                "Package": self._packages(parcels, "PackagingType"),
            }}}
        data, _ = self.http.json("POST", f"{self.host}/api/rating/{self.version}/Shop", self._headers(), body)
        out = []
        for r in _list((data.get("RateResponse") or {}).get("RatedShipment")):
            code = (r.get("Service") or {}).get("Code", "")
            neg = ((r.get("NegotiatedRateCharges") or {}).get("TotalCharge") or {}).get("MonetaryValue")
            amount = float(neg or (r.get("TotalCharges") or {}).get("MonetaryValue") or 0)
            days = (r.get("GuaranteedDelivery") or {}).get("BusinessDaysInTransit")
            out.append(Rate("ups", code, SERVICES.get(code, f"UPS service {code}"), amount,
                            (r.get("TotalCharges") or {}).get("CurrencyCode", "USD"), int(days) if days else None))
        return out

    def buy(self, ship_from: Address, ship_to: Address, parcels: list[Parcel], service: str,
            reference: str = "") -> list[Label]:
        fmt = env("UPS_LABEL_FORMAT", "GIF").upper()  # GIF or ZPL
        body = {"ShipmentRequest": {
            "Request": {"RequestOption": "nonvalidate", "SubVersion": self.version.lstrip("v")},
            "Shipment": {
                "Description": reference[:35] or "Parts",
                "Shipper": self._party(ship_from, shipper=True), "ShipFrom": self._party(ship_from),
                "ShipTo": self._party(ship_to),
                "PaymentInformation": {"ShipmentCharge": [{"Type": "01", "BillShipper": {"AccountNumber": env("UPS_ACCOUNT")}}]},
                "Service": {"Code": service, "Description": SERVICES.get(service, "")},
                "ShipmentRatingOptions": {"NegotiatedRatesIndicator": "Y"},
                "ReferenceNumber": {"Value": reference[:35]} if reference else None,
                "Package": self._packages(parcels, "Packaging"),
            },
            "LabelSpecification": {"LabelImageFormat": {"Code": fmt}, "LabelStockSize": {"Height": "6", "Width": "4"}},
        }}
        if not reference:
            del body["ShipmentRequest"]["Shipment"]["ReferenceNumber"]
        data, _ = self.http.json("POST", f"{self.host}/api/shipments/{self.version}/ship", self._headers(), body)
        results = ((data.get("ShipmentResponse") or {}).get("ShipmentResults")) or {}
        ident = results.get("ShipmentIdentificationNumber", "")
        charges = results.get("NegotiatedRateCharges") or results.get("ShipmentCharges") or {}
        total = (charges.get("TotalCharge") or charges.get("TotalCharges") or {}).get("MonetaryValue")
        labels = []
        pkgs = _list(results.get("PackageResults"))
        for i, pkg in enumerate(pkgs):
            img = ((pkg.get("ShippingLabel") or {}).get("GraphicImage")) or ""
            if not img:
                raise CarrierError("UPS created the shipment but returned no label image")
            labels.append(Label("ups", service, pkg.get("TrackingNumber", ""), base64.b64decode(img),
                                "zpl" if fmt == "ZPL" else "gif",
                                cost=float(total) / len(pkgs) if total else None, shipment_id=ident))
        if not labels:
            raise CarrierError("UPS returned no packages")
        return labels

    def void(self, tracking: str, shipment_id: str = "") -> None:
        ident = shipment_id or tracking
        self.http.json("DELETE", f"{self.host}/api/shipments/{self.version}/void/cancel/{ident}", self._headers())

    def track(self, tracking: str) -> TrackInfo:
        data, _ = self.http.json("GET", f"{self.host}/api/track/v1/details/{tracking}?locale=en_US", self._headers())
        ship = (_list((data.get("trackResponse") or {}).get("shipment")) or [{}])[0]
        pkg = (_list(ship.get("package")) or [{}])[0]
        cur = pkg.get("currentStatus") or {}
        desc = cur.get("description") or "No updates yet"
        delivered = cur.get("code") in ("011", "D") or "deliver" in desc.lower() and "out for" not in desc.lower()
        events = [{"at": f"{a.get('date', '')} {a.get('time', '')}".strip(),
                   "text": (a.get("status") or {}).get("description", ""),
                   "where": ((a.get("location") or {}).get("address") or {}).get("city", "")}
                  for a in _list(pkg.get("activity"))[:10]]
        return TrackInfo("delivered" if delivered else "in_transit", desc, delivered, events)


def today() -> str:
    return date.today().isoformat()
