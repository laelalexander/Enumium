"""FedEx, direct: OAuth + the FedEx REST APIs, with the shop's FedEx account.

Environment (/etc/pyslate.env):
  FEDEX_CLIENT_ID, FEDEX_CLIENT_SECRET   API key and secret key from developer.fedex.com
  FEDEX_ACCOUNT                          9-digit FedEx account number (bills the postage)
  FEDEX_ENV=test                         use apis-sandbox.fedex.com until labels look right
"""

from __future__ import annotations

import base64
from datetime import date

from .base import Address, CarrierError, Http, Label, NotConfigured, Parcel, Rate, TOKENS, TrackInfo, env

SERVICES = {
    "FEDEX_GROUND": "FedEx Ground", "GROUND_HOME_DELIVERY": "FedEx Home Delivery",
    "FEDEX_EXPRESS_SAVER": "FedEx Express Saver", "FEDEX_2_DAY": "FedEx 2Day", "FEDEX_2_DAY_AM": "FedEx 2Day A.M.",
    "STANDARD_OVERNIGHT": "FedEx Standard Overnight", "PRIORITY_OVERNIGHT": "FedEx Priority Overnight",
    "FIRST_OVERNIGHT": "FedEx First Overnight",
}


class FedEx:
    code, name = "fedex", "FedEx"

    def __init__(self, http: Http):
        self.http = http

    def configured(self) -> bool:
        return bool(env("FEDEX_CLIENT_ID") and env("FEDEX_CLIENT_SECRET") and env("FEDEX_ACCOUNT"))

    @property
    def host(self) -> str:
        return "https://apis-sandbox.fedex.com" if env("FEDEX_ENV", "production") == "test" else "https://apis.fedex.com"

    def _token(self) -> str:
        if not self.configured():
            raise NotConfigured("FedEx isn't connected")

        def fetch():
            data, _ = self.http.json("POST", f"{self.host}/oauth/token", form={
                "grant_type": "client_credentials", "client_id": env("FEDEX_CLIENT_ID"),
                "client_secret": env("FEDEX_CLIENT_SECRET")})
            if not data.get("access_token"):
                raise CarrierError("FedEx sign-in failed")
            return data["access_token"], data.get("expires_in", 3599)

        return TOKENS.get(f"fedex:{self.host}", fetch)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token()}", "X-locale": "en_US"}

    def check(self) -> str:
        self._token()
        return f"Signed in to FedEx ({'sandbox' if 'sandbox' in self.host else 'production'})"

    @staticmethod
    def _address(a: Address, residential: bool = False) -> dict:
        out = {"streetLines": a.street[:3], "city": a.city, "stateOrProvinceCode": a.state,
               "postalCode": a.postal, "countryCode": a.country}
        if residential:
            out["residential"] = True
        return out

    def _party(self, a: Address, residential: bool = False) -> dict:
        contact = {"personName": a.name[:70], "phoneNumber": "".join(ch for ch in a.phone if ch.isdigit())[:15] or "0000000000"}
        if a.company:
            contact["companyName"] = a.company[:35]
        if a.email:
            contact["emailAddress"] = a.email
        return {"contact": contact, "address": self._address(a, residential)}

    @staticmethod
    def _packages(parcels: list[Parcel]) -> list[dict]:
        out = []
        for i, p in enumerate(parcels, start=1):
            item = {"sequenceNumber": i, "weight": {"units": "LB", "value": p.weight_lb}}
            dims = p.dims_in()
            if dims:
                item["dimensions"] = {"length": int(dims[0]), "width": int(dims[1]), "height": int(dims[2]), "units": "IN"}
            out.append(item)
        return out

    def rates(self, ship_from: Address, ship_to: Address, parcels: list[Parcel]) -> list[Rate]:
        body = {
            "accountNumber": {"value": env("FEDEX_ACCOUNT")},
            "requestedShipment": {
                "shipper": {"address": self._address(ship_from)},
                "recipient": {"address": self._address(ship_to, residential=not ship_to.company)},
                "pickupType": "USE_SCHEDULED_PICKUP", "rateRequestType": ["ACCOUNT", "LIST"],
                "requestedPackageLineItems": self._packages(parcels),
            },
        }
        data, _ = self.http.json("POST", f"{self.host}/rate/v1/rates/quotes", self._headers(), body)
        out = []
        for d in (data.get("output") or {}).get("rateReplyDetails") or []:
            details = d.get("ratedShipmentDetails") or [{}]
            acct = next((x for x in details if x.get("rateType") == "ACCOUNT"), details[0])
            amount = acct.get("totalNetCharge") or acct.get("totalNetFedExCharge") or 0
            svc = d.get("serviceType", "")
            out.append(Rate("fedex", svc, d.get("serviceName") or SERVICES.get(svc, svc), float(amount),
                            acct.get("currency", "USD")))
        return out

    def buy(self, ship_from: Address, ship_to: Address, parcels: list[Parcel], service: str,
            reference: str = "") -> list[Label]:
        fmt = env("FEDEX_LABEL_FORMAT", "PNG").upper()  # PNG, PDF or ZPLII
        stock = "STOCK_4X6" if fmt == "ZPLII" else "PAPER_4X6"
        pkgs = self._packages(parcels)
        if reference:
            for p in pkgs:
                p["customerReferences"] = [{"customerReferenceType": "CUSTOMER_REFERENCE", "value": reference[:30]}]
        body = {
            "labelResponseOptions": "LABEL",
            "accountNumber": {"value": env("FEDEX_ACCOUNT")},
            "requestedShipment": {
                "shipper": self._party(ship_from),
                "recipients": [self._party(ship_to, residential=not ship_to.company)],
                "shipDatestamp": date.today().isoformat(),
                "serviceType": service, "packagingType": "YOUR_PACKAGING", "pickupType": "USE_SCHEDULED_PICKUP",
                "blockInsightVisibility": False,
                "shippingChargesPayment": {"paymentType": "SENDER"},
                "labelSpecification": {"imageType": fmt, "labelStockType": stock},
                "requestedPackageLineItems": pkgs,
            },
        }
        data, _ = self.http.json("POST", f"{self.host}/ship/v1/shipments", self._headers(), body)
        shipments = (data.get("output") or {}).get("transactionShipments") or []
        if not shipments:
            raise CarrierError("FedEx returned no shipment")
        ship = shipments[0]
        rating = ((ship.get("completedShipmentDetail") or {}).get("shipmentRating") or {}).get("shipmentRateDetails") or [{}]
        total = rating[0].get("totalNetCharge")
        pieces = ship.get("pieceResponses") or []
        labels = []
        for piece in pieces:
            doc = next((d for d in piece.get("packageDocuments") or [] if d.get("encodedLabel")), None)
            if doc is None:
                raise CarrierError("FedEx created the shipment but returned no label image")
            labels.append(Label("fedex", service, piece.get("trackingNumber", ""), base64.b64decode(doc["encodedLabel"]),
                                {"PNG": "png", "PDF": "pdf", "ZPLII": "zpl"}.get(fmt, "png"),
                                cost=float(total) / len(pieces) if total else None,
                                shipment_id=ship.get("masterTrackingNumber", "")))
        if not labels:
            raise CarrierError("FedEx returned no packages")
        return labels

    def void(self, tracking: str, shipment_id: str = "") -> None:
        data, _ = self.http.json("PUT", f"{self.host}/ship/v1/shipments/cancel", self._headers(), {
            "accountNumber": {"value": env("FEDEX_ACCOUNT")}, "trackingNumber": shipment_id or tracking,
            "deletionControl": "DELETE_ALL_PACKAGES"})
        if not (data.get("output") or {}).get("cancelledShipment", True):
            raise CarrierError("FedEx didn't cancel the shipment")

    def track(self, tracking: str) -> TrackInfo:
        data, _ = self.http.json("POST", f"{self.host}/track/v1/trackingnumbers", self._headers(), {
            "includeDetailedScans": True, "trackingInfo": [{"trackingNumberInfo": {"trackingNumber": tracking}}]})
        results = ((data.get("output") or {}).get("completeTrackResults") or [{}])[0].get("trackResults") or [{}]
        latest = results[0].get("latestStatusDetail") or {}
        desc = latest.get("description") or latest.get("statusByLocale") or "No updates yet"
        delivered = latest.get("code") == "DL"
        events = [{"at": e.get("date", ""), "text": e.get("eventDescription", ""),
                   "where": (e.get("scanLocation") or {}).get("city", "")} for e in (results[0].get("scanEvents") or [])[:10]]
        return TrackInfo("delivered" if delivered else "in_transit", desc, delivered, events)
