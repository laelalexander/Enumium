"""Direct UPS, FedEx and USPS connections, tested against fake carrier servers."""

import base64
import json

import pytest
from fastapi.testclient import TestClient

from pyslate import carriers, services
from pyslate.carriers.base import TOKENS
from pyslate.carriers.fedex import FedEx
from pyslate.carriers.ups import UPS
from pyslate.carriers.usps import USPS, parse_label_response
from pyslate.models import CarrierLabel, Order

from test_shopops import app, order_for, shop  # noqa: F401  (fixtures)

PNG = b"\x89PNG\r\n\x1a\nfake"
FROM = carriers.Address("Pyslate", ["100 Shop Rd"], "Dallas", "TX", "75201", phone="214-555-0100", company="Pyslate")
TO = carriers.Address("Gus Guest", ["5 Elm St", "Apt 2"], "Austin", "TX", "78701-1234")
BOXES = [carriers.Parcel(900, 300, 200, 100), carriers.Parcel(450)]


class FakeHttp(carriers.Http):
    def __init__(self, routes):
        super().__init__()
        self.routes, self.calls = routes, []

    def send(self, method, url, headers, body):
        self.calls.append((method, url, headers, json.loads(body) if body and body[:1] == b"{" else body))
        for (m, part), resp in self.routes.items():
            if m == method and part in url:
                status, data = resp if isinstance(resp, tuple) else (200, resp)
                if isinstance(data, tuple):  # (headers, raw bytes)
                    return status, data[0], data[1]
                return status, {"Content-Type": "application/json"}, json.dumps(data).encode()
        raise AssertionError(f"unexpected {method} {url}")


@pytest.fixture(autouse=True)
def carrier_env(monkeypatch):
    TOKENS._tokens.clear()
    for k, v in {"UPS_CLIENT_ID": "u", "UPS_CLIENT_SECRET": "s", "UPS_ACCOUNT": "A1B2C3", "UPS_ENV": "test",
                 "FEDEX_CLIENT_ID": "f", "FEDEX_CLIENT_SECRET": "s", "FEDEX_ACCOUNT": "123456789", "FEDEX_ENV": "test",
                 "USPS_CLIENT_ID": "p", "USPS_CLIENT_SECRET": "s", "USPS_CRID": "1", "USPS_MID": "2",
                 "USPS_EPS_ACCOUNT": "3", "USPS_ENV": "test"}.items():
        monkeypatch.setenv(k, v)
    yield
    TOKENS._tokens.clear()


def test_addresses_parse_from_order_text():
    a = carriers.parse_us_address("Gus Guest", "5 Elm St\nAustin, TX 78701")
    assert (a.street, a.city, a.state, a.postal) == (["5 Elm St"], "Austin", "TX", "78701")
    b = carriers.parse_us_address("Ada", "Acme Inc, 1 Main St, Suite 4, Dallas, TX 75201-1234")
    assert b.city == "Dallas" and b.zip5 == "75201" and b.zip4 == "1234"
    with pytest.raises(carriers.CarrierError):
        carriers.parse_us_address("Nope", "somewhere")


def test_ups_rates_buy_void_track():
    http = FakeHttp({
        ("POST", "/security/v1/oauth/token"): {"access_token": "tok", "expires_in": "14399"},
        ("POST", "/api/rating/"): {"RateResponse": {"RatedShipment": [
            {"Service": {"Code": "03"}, "TotalCharges": {"MonetaryValue": "14.20", "CurrencyCode": "USD"},
             "NegotiatedRateCharges": {"TotalCharge": {"MonetaryValue": "11.05"}}},
            {"Service": {"Code": "01"}, "TotalCharges": {"MonetaryValue": "61.00"},
             "GuaranteedDelivery": {"BusinessDaysInTransit": "1"}}]}},
        ("POST", "/api/shipments/"): {"ShipmentResponse": {"ShipmentResults": {
            "ShipmentIdentificationNumber": "1ZSHIP", "ShipmentCharges": {"TotalCharges": {"MonetaryValue": "22.10"}},
            "PackageResults": [{"TrackingNumber": "1Z1", "ShippingLabel": {"GraphicImage": base64.b64encode(b"GIF1").decode()}},
                               {"TrackingNumber": "1Z2", "ShippingLabel": {"GraphicImage": base64.b64encode(b"GIF2").decode()}}]}}},
        ("DELETE", "/void/cancel/1ZSHIP"): {"VoidShipmentResponse": {}},
        ("GET", "/api/track/v1/details/1Z1"): {"trackResponse": {"shipment": [{"package": [
            {"currentStatus": {"code": "011", "description": "Delivered"}, "activity": []}]}]}},
    })
    ups = UPS(http)
    rates = ups.rates(FROM, TO, BOXES)
    assert [(r.service, r.amount) for r in rates] == [("03", 11.05), ("01", 61.0)] and rates[1].days == 1
    assert http.calls[0][1].startswith("https://wwwcie.ups.com") and http.calls[0][2]["x-merchant-id"] == "A1B2C3"
    sent = http.calls[1][3]["RateRequest"]["Shipment"]
    assert sent["Shipper"]["ShipperNumber"] == "A1B2C3" and len(sent["Package"]) == 2
    assert sent["Package"][0]["Dimensions"]["Length"] == "12" and "Dimensions" not in sent["Package"][1]
    labels = ups.buy(FROM, TO, BOXES, "03", reference="Order 1001")
    assert [lab.tracking for lab in labels] == ["1Z1", "1Z2"] and labels[0].data == b"GIF1" and labels[0].fmt == "gif"
    assert labels[0].cost == pytest.approx(11.05) and labels[0].shipment_id == "1ZSHIP"
    ups.void("1Z1", "1ZSHIP")
    assert ups.track("1Z1").delivered
    assert sum(1 for c in http.calls if "oauth" in c[1]) == 1  # the token is reused


def test_fedex_rates_and_label():
    http = FakeHttp({
        ("POST", "/oauth/token"): {"access_token": "tok", "expires_in": 3599},
        ("POST", "/rate/v1/rates/quotes"): {"output": {"rateReplyDetails": [
            {"serviceType": "FEDEX_GROUND", "serviceName": "FedEx Ground", "ratedShipmentDetails": [
                {"rateType": "LIST", "totalNetCharge": 19.5}, {"rateType": "ACCOUNT", "totalNetCharge": 13.25}]}]}},
        ("POST", "/ship/v1/shipments"): {"output": {"transactionShipments": [{
            "masterTrackingNumber": "7940",
            "completedShipmentDetail": {"shipmentRating": {"shipmentRateDetails": [{"totalNetCharge": 13.25}]}},
            "pieceResponses": [{"trackingNumber": "7940", "packageDocuments": [
                {"contentType": "LABEL", "encodedLabel": base64.b64encode(PNG).decode()}]}]}]}},
        ("PUT", "/ship/v1/shipments/cancel"): {"output": {"cancelledShipment": True}},
        ("POST", "/track/v1/trackingnumbers"): {"output": {"completeTrackResults": [{"trackResults": [
            {"latestStatusDetail": {"code": "IT", "description": "In transit"}, "scanEvents": []}]}]}},
        ("POST", "/fail"): (400, {}),
    })
    fx = FedEx(http)
    rates = fx.rates(FROM, TO, BOXES[:1])
    assert rates[0].amount == 13.25 and rates[0].name == "FedEx Ground"
    assert http.calls[0][1] == "https://apis-sandbox.fedex.com/oauth/token"
    lab = fx.buy(FROM, TO, BOXES[:1], "FEDEX_GROUND", reference="Order 1001")[0]
    assert lab.tracking == "7940" and lab.data == PNG and lab.fmt == "png"
    body = http.calls[-1][3]["requestedShipment"]
    assert body["serviceType"] == "FEDEX_GROUND" and body["recipients"][0]["address"]["postalCode"] == "78701-1234"
    fx.void("7940")
    info = fx.track("7940")
    assert not info.delivered and info.detail == "In transit"


def test_fedex_error_is_readable():
    http = FakeHttp({("POST", "/oauth/token"): (401, {"errors": [{"code": "NOT.AUTHORIZED", "message": "Bad client"}]})})
    with pytest.raises(carriers.CarrierError, match="Bad client"):
        FedEx(http).check()


def multipart(meta: dict, image: bytes) -> tuple[dict, bytes]:
    b = "BOUNDARY42"
    raw = (f"--{b}\r\nContent-Disposition: form-data; name=\"labelMetadata\"\r\nContent-Type: application/json\r\n\r\n"
           f"{json.dumps(meta)}\r\n--{b}\r\nContent-Disposition: form-data; name=\"labelImage\"; filename=\"label.pdf\"\r\n"
           f"Content-Type: application/pdf\r\n\r\n").encode() + image + f"\r\n--{b}--\r\n".encode()
    return {"Content-Type": f"multipart/form-data; boundary={b}"}, raw


def test_usps_multipart_label_and_rates():
    meta, raw = {"trackingNumber": "9400111", "postage": 8.4}, b"%PDF-1.7 label"
    headers, body = multipart(meta, raw)
    assert parse_label_response(headers, body) == (meta, raw)
    http = FakeHttp({
        ("POST", "/oauth2/v3/token"): {"access_token": "tok", "expires_in": 28799},
        ("POST", "/payments/v3/payment-authorization"): {"paymentAuthorizationToken": "pay"},
        ("POST", "/prices/v3/base-rates/search"): {"totalBasePrice": 7.5},
        ("POST", "/labels/v3/label"): (200, (headers, body)),
        ("DELETE", "/labels/v3/label/9400111"): (204, {}),
    })
    usps = USPS(http)
    rates = usps.rates(FROM, TO, BOXES)
    assert len(rates) == 3 and all(r.amount == 15.0 for r in rates)
    labels = usps.buy(FROM, TO, BOXES[:1], "USPS_GROUND_ADVANTAGE")
    assert labels[0].tracking == "9400111" and labels[0].fmt == "pdf" and labels[0].cost == 8.4
    call = next(c for c in http.calls if c[1].endswith("/labels/v3/label"))
    assert call[2]["X-Payment-Authorization-Token"] == "pay"
    sent = call[3]
    assert sent["toAddress"]["ZIPCode"] == "78701" and sent["toAddress"]["ZIPPlus4"] == "1234"
    assert sent["toAddress"]["secondaryAddress"] == "Apt 2"
    usps.void("9400111")


# ---- the shop console with a fake carrier ------------------------------------------------


class FakeCarrier:
    code, name = "ups", "UPS"

    def __init__(self):
        self.voided = []

    def configured(self):
        return True

    def rates(self, ship_from, ship_to, parcels):
        assert ship_to.city == "Austin" and ship_from.phone
        return [carriers.Rate("ups", "03", "UPS Ground", 9.99 * len(parcels)),
                carriers.Rate("ups", "01", "UPS Next Day Air", 48.0, days=1)]

    def buy(self, ship_from, ship_to, parcels, service, reference=""):
        return [carriers.Label("ups", service, f"1ZFAKE{i}", PNG, "png", cost=9.99, shipment_id="1ZSHIP")
                for i in range(1, len(parcels) + 1)]

    def void(self, tracking, shipment_id=""):
        self.voided.append(tracking)

    def track(self, tracking):
        return carriers.TrackInfo("in_transit", "Arrived at facility, Waco TX")


def set_ship_from(app, phone="214-555-0100"):
    with app.state.session_factory() as db:
        data = dict(services.get_profile(db).data)
        data["ship_from"] = {"name": "Pyslate", "address": "100 Shop Rd\nDallas, TX 75201", "phone": phone}
        services.save_profile(db, data)
        db.commit()


def test_postage_not_connected(app, shop, cube_stl, monkeypatch):
    for k in ("UPS_CLIENT_ID", "FEDEX_CLIENT_ID", "USPS_CLIENT_ID"):
        monkeypatch.delenv(k)
    number, _ = order_for(app, cube_stl, made=True)
    page = shop.get(f"/admin/order/{number}/postage").text
    assert "No carrier connected yet" in page and "UPS_CLIENT_ID" in page and "Pack the order first" in page


def test_buy_postage_print_void_track(app, shop, cube_stl):
    fake = FakeCarrier()
    app.state.carrier_registry = {"ups": fake}
    number, token = order_for(app, cube_stl, made=True)
    shop.post(f"/admin/order/{number}/pack", data={"packages": "2", "weight_g": "900", "dims": "300 x 200 x 100"})
    assert "Buy postage" in shop.get("/admin/shipping").text

    set_ship_from(app, phone="")
    assert "phone number" in shop.get(f"/admin/order/{number}/postage").text
    set_ship_from(app)
    page = shop.get(f"/admin/order/{number}/postage").text
    assert "Couldn" in page and 'value="5 Elm St"' in page  # the order has no ZIP, so the shop fixes it here
    to = {"to_name": "Gus Guest", "to_street1": "5 Elm St", "to_city": "Austin", "to_state": "TX", "to_postal": "78701"}
    page = shop.get(f"/admin/order/{number}/postage", params=to).text
    assert "UPS Ground" in page and "$19.98" in page and "Buy label" in page and 'value="Austin"' in page

    r = shop.post(f"/admin/order/{number}/postage", data={"carrier": "ups", "service": "03", "service_name": "UPS Ground", **to}, follow_redirects=False)
    assert r.headers["location"] == f"/admin/order/{number}/labels"
    labels = shop.get(f"/admin/order/{number}/labels").text
    assert labels.count('class="carrier-label"') == 2 and "1ZFAKE2" in labels and "$9.99" in labels
    with app.state.session_factory() as db:
        order = db.query(Order).filter_by(number=number).one()
        assert order.status == "shipped" and order.tracking == "1ZFAKE1"
        lab = db.query(CarrierLabel).filter_by(tracking="1ZFAKE1").one()
        lab_id, (other_id,) = lab.id, [x.id for x in db.query(CarrierLabel).filter_by(tracking="1ZFAKE2")]
    img = shop.get(f"/admin/carrier-label/{lab_id}")
    assert img.status_code == 200 and img.content == PNG and img.headers["content-type"] == "image/png"
    assert "UPS Ground" in TestClient(app).get(f"/order/{number}?t={token}").text

    shop.post(f"/admin/order/{number}/track", data={"back": "/admin/shipping"})
    assert "Waco TX" in shop.get("/admin/shipping").text
    assert "Waco TX" in TestClient(app).get(f"/order/{number}?t={token}").text

    # Voiding every label puts the order back in packing.
    shop.post(f"/admin/carrier-label/{lab_id}/void")
    shop.post(f"/admin/carrier-label/{other_id}/void")
    assert fake.voided == ["1ZFAKE1", "1ZFAKE2"]
    with app.state.session_factory() as db:
        assert db.query(Order).filter_by(number=number).one().status == "finishing"
    assert "void" in shop.get(f"/admin/order/{number}/labels").text


def test_buying_needs_a_connected_carrier(app, shop, cube_stl):
    app.state.carrier_registry = {"ups": FakeCarrier()}
    number, _ = order_for(app, cube_stl, made=True)
    shop.post(f"/admin/order/{number}/pack", data={"packages": "1", "weight_g": "300"})
    r = shop.post(f"/admin/order/{number}/postage", data={"carrier": "fedex", "service": "X"}, follow_redirects=False)
    assert "connected" in r.headers["location"]
