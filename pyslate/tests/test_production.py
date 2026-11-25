"""The fab shop's production side: sending jobs to machines and the shop agent."""

import io
import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pyslate import jobfiles, services
from pyslate.app import create_app
from pyslate.config import Settings
from pyslate.models import Job, JobRun, Order, Quote
from pyslate.shop_agent.agent import Agent, ApiError
from pyslate.shop_agent.drivers import Cancelled, Driver, Handoff
from pyslate.shop_agent.drivers.marlin import MarlinDriver, checksum, clean_lines

AGENT = {"Authorization": "Bearer agent-secret", "X-Agent-Name": "yaeger"}


@pytest.fixture
def app(tmp_path):
    cfg = Settings(data_dir=tmp_path / "data", admin_token="shop-secret", secret_key="k" * 32)
    cfg.stripe_secret_key = None
    cfg.agent_token = "agent-secret"
    return create_app(cfg)


@pytest.fixture
def client(app):
    c = TestClient(app)
    assert c.post("/admin/login", data={"token": "shop-secret"}, follow_redirects=False).status_code == 303
    return c


def paid_order(app, *parts, quantity=1, material=None) -> tuple[int, list[str]]:
    """Order the parts, mark it paid, and return (order number, job ids)."""
    cfg = app.state.settings
    with app.state.session_factory() as db:
        quote = Quote()
        db.add(quote)
        for path in parts:
            part = services.store_part(db, cfg.upload_dir, path.name, path)
            line = services.add_part_to_quote(db, quote, part)
            db.flush()
            services.update_line(db, line, material or line.material_id, quantity)
        order = services.place_order(db, quote, "b@example.com", "Buyer", "1 Main St")
        services.mark_paid(db, order)
        return order.number, [j.id for j in order.jobs]


def job_state(app, job_id):
    with app.state.session_factory() as db:
        job = db.get(Job, job_id)
        return job.state, job.order.status, job.copies_done


# ---- files -------------------------------------------------------------------


def test_layout_fits_copies_on_the_bed():
    lay = jobfiles.plan_layout(100, 100, [426, 320], 20)
    assert lay.per_sheet == 12 and lay.sheets == 2  # 4 x 3 fit on an M2
    rotated = jobfiles.plan_layout(300, 50, [120, 400], 3)  # only fits turned a quarter
    assert rotated.rotated and rotated.per_sheet == 2 and rotated.sheets == 2
    with pytest.raises(jobfiles.JobFileError):
        jobfiles.plan_layout(700, 100, [426, 320], 1)


def test_svg_and_dxf_sheets(tmp_path, square_dxf, plate_stl):
    outline = jobfiles.outline_for(square_dxf)
    assert round(outline.width) == 100 and round(outline.height) == 100
    lay = jobfiles.plan_layout(outline.width, outline.height, [426, 320], 4)
    svg = tmp_path / "s.svg"
    jobfiles.write_svg(outline, lay, svg, "Order 1001")
    text = svg.read_text()
    assert 'width="' in text and "mm" in text and text.count("<path") == 8  # square + hole, 4 times
    dxf = tmp_path / "s.dxf"
    jobfiles.write_dxf(outline, lay, dxf)
    import ezdxf

    assert len(ezdxf.readfile(dxf).modelspace().query("LWPOLYLINE")) == 8
    flat = jobfiles.outline_for(plate_stl)  # a flat STL is sectioned into its outline
    assert round(flat.width) == 60 and round(flat.height) == 40 and len(flat.paths) == 2


# ---- the production board and runs --------------------------------------------


def test_board_lists_jobs_per_machine(app, client, cube_stl, plate_stl):
    number, _ = paid_order(app, cube_stl, plate_stl)
    page = client.get("/admin/production").text
    assert "cube.stl" in page and "plate.stl" in page
    assert "Send to machine" in page and "No shop agent connected" in page
    assert "plate.stl" in client.get("/admin/production?line=laser").text
    assert "cube.stl" not in client.get("/admin/production?line=laser").text


def test_send_laser_job_and_agent_finishes_it(app, client, plate_stl):
    number, (job_id,) = paid_order(app, plate_stl, quantity=4)
    r = client.post(f"/admin/job/{job_id}/send", data={"machine_id": "m2", "copies": "4", "passes": "2"},
                    follow_redirects=False)
    assert r.status_code == 303 and "error" not in r.headers["location"]
    assert job_state(app, job_id)[0] == "sent"
    svg = client.get(f"/admin/job/{job_id}/file/svg")
    assert svg.status_code == 200 and svg.text.count("<path") == 8

    # The agent sees and claims it; a second claim is refused.
    runs = client.get("/api/agent/runs?machines=m2,x1", headers=AGENT).json()["runs"]
    assert len(runs) == 1 and runs[0]["settings"]["passes"] == 2 and runs[0]["copies"] == 4
    run_id = runs[0]["id"]
    assert client.post(f"/api/agent/runs/{run_id}/claim", headers=AGENT).status_code == 200
    assert client.post(f"/api/agent/runs/{run_id}/claim", headers=AGENT).status_code == 409
    f = client.get(f"/api/agent/runs/{run_id}/file", headers=AGENT)
    assert f.status_code == 200 and "<svg" in f.text

    client.post(f"/api/agent/runs/{run_id}/update", headers=AGENT, json={"state": "running", "progress": 40})
    assert job_state(app, job_id)[:2] == ("running", "making")
    client.post(f"/api/agent/runs/{run_id}/update", headers=AGENT, json={"state": "done", "message": "ok"})
    assert job_state(app, job_id) == ("done", "finishing", 4)


def test_partial_runs_leave_the_rest_queued(app, client, cube_stl):
    _, (job_id,) = paid_order(app, cube_stl, quantity=3)
    client.post(f"/admin/job/{job_id}/send", data={"machine_id": "bambu", "copies": "2"})
    with app.state.session_factory() as db:
        run = db.query(JobRun).one()
        run_id = run.id
    client.post(f"/api/agent/runs/{run_id}/claim", headers=AGENT)
    client.post(f"/api/agent/runs/{run_id}/update", headers=AGENT, json={"state": "done"})
    assert job_state(app, job_id) == ("queued", "making", 2)
    bad = client.post(f"/admin/job/{job_id}/send", data={"machine_id": "bambu", "copies": "2"}, follow_redirects=False)
    assert "between+1+and+1" in bad.headers["location"] or "between%201%20and%201" in bad.headers["location"]
    client.post(f"/admin/job/{job_id}/send", data={"machine_id": "a8s", "copies": "1"})
    with app.state.session_factory() as db:
        run2 = db.query(JobRun).filter(JobRun.state == "pending").one()
        assert run2.machine_id == "a8s"
    # The shop closes the run by hand (e.g. printed from the SD card).
    client.post(f"/admin/run/{run2.id}/close", data={"state": "done"})
    assert job_state(app, job_id) == ("done", "finishing", 3)


def test_wrong_machine_and_unpaid_are_refused(app, client, cube_stl):
    _, (job_id,) = paid_order(app, cube_stl)
    r = client.post(f"/admin/job/{job_id}/send", data={"machine_id": "x1", "copies": "1"}, follow_redirects=False)
    assert "production+line" in r.headers["location"] or "production%20line" in r.headers["location"]
    assert job_state(app, job_id)[0] == "queued"


def test_cancel_pending_and_running(app, client, cube_stl):
    _, (job_id,) = paid_order(app, cube_stl, quantity=2)
    client.post(f"/admin/job/{job_id}/send", data={"machine_id": "bambu", "copies": "1"})
    with app.state.session_factory() as db:
        run_id = db.query(JobRun).one().id
    client.post(f"/admin/run/{run_id}/cancel")
    assert job_state(app, job_id)[0] == "queued"

    client.post(f"/admin/job/{job_id}/send", data={"machine_id": "bambu", "copies": "1"})
    with app.state.session_factory() as db:
        run_id = db.query(JobRun).filter(JobRun.state == "pending").one().id
    client.post(f"/api/agent/runs/{run_id}/claim", headers=AGENT)
    client.post(f"/api/agent/runs/{run_id}/update", headers=AGENT, json={"state": "running"})
    client.post(f"/admin/run/{run_id}/cancel")
    # The agent's next progress report learns it should stop.
    r = client.post(f"/api/agent/runs/{run_id}/update", headers=AGENT, json={"state": "running", "progress": 50})
    assert r.json()["state"] == "cancel_requested"
    client.post(f"/api/agent/runs/{run_id}/update", headers=AGENT, json={"state": "cancelled"})
    assert job_state(app, job_id)[0] == "queued"


def test_review_job_gets_a_machine(app, client, cube_stl):
    _, (job_id,) = paid_order(app, cube_stl)
    with app.state.session_factory() as db:
        job = db.get(Job, job_id)
        job.state, job.machine_id, job.line = "review", None, "review"
        db.commit()
    assert "Needs a machine" in client.get("/admin/production").text
    client.post(f"/admin/job/{job_id}/assign", data={"machine_id": "a8s"})
    with app.state.session_factory() as db:
        job = db.get(Job, job_id)
        assert (job.state, job.machine_id, job.line) == ("queued", "a8s", "print")


def test_agent_api_needs_the_token(app, tmp_path):
    c = TestClient(app)
    assert c.get("/api/agent/runs").status_code == 401
    assert c.get("/api/agent/runs", headers={"Authorization": "Bearer nope"}).status_code == 401
    cfg = Settings(data_dir=tmp_path / "d2", admin_token="x", secret_key="k" * 32)
    cfg.agent_token = None
    assert TestClient(create_app(cfg)).get("/api/agent/runs", headers=AGENT).status_code == 503


def test_heartbeat_shows_machine_status(app, client):
    r = client.post("/api/agent/heartbeat", headers=AGENT,
                    json={"machines": [{"id": "x1", "state": "idle", "detail": "On the network", "driver": "xtool"}]})
    assert r.status_code == 200
    status = client.get("/admin/production/status.json").json()
    assert status["machines"]["x1"]["state"] == "idle" and status["machines"]["x1"]["online"]
    page = client.get("/admin/production").text
    assert "Shop agent online: yaeger" in page
    assert "On the network" in client.get("/admin/agent").text


def test_agent_download_has_config(client):
    r = client.get("/admin/agent/download")
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = set(z.namelist())
    assert {"agent.json", "run-agent.bat", "README.md", "shop_agent/agent.py", "shop_agent/drivers/marlin.py"} <= names
    cfg = json.loads(z.read("agent.json"))
    assert cfg["token"] == "agent-secret"
    assert {m["id"]: m["driver"] for m in cfg["machines"]}["a8s"] == "marlin"


# ---- the shop agent ---------------------------------------------------------------


class ClientApi:
    """The agent's Api, backed by the test client instead of HTTPS."""

    def __init__(self, client):
        self.c = client
        self.base = "test"

    def _json(self, r):
        if r.status_code >= 400:
            raise ApiError(r.status_code, r.text)
        return r.json()

    def heartbeat(self, machines):
        return self._json(self.c.post("/api/agent/heartbeat", headers=AGENT, json={"machines": machines}))

    def pending(self, ids):
        return self._json(self.c.get("/api/agent/runs?machines=" + ",".join(ids), headers=AGENT))["runs"]

    def claim(self, run_id):
        return self._json(self.c.post(f"/api/agent/runs/{run_id}/claim", headers=AGENT))

    def get(self, run_id):
        return self._json(self.c.get(f"/api/agent/runs/{run_id}", headers=AGENT))

    def update(self, run_id, state, progress=None, message=""):
        return self._json(self.c.post(f"/api/agent/runs/{run_id}/update", headers=AGENT,
                                      json={"state": state, "progress": progress, "message": message}))

    def download(self, run, target: Path):
        target.write_bytes(self.c.get(f"/api/agent/runs/{run['id']}/file", headers=AGENT).content)
        return target


class FakeDriver(Driver):
    name = "fake"
    outcome = "done"
    seen: list = []

    def status(self):
        return {"state": "idle", "detail": "fake"}

    def run(self, run, path, ctx):
        FakeDriver.seen.append((run["machine_id"], path.read_bytes()[:5]))
        ctx.progress(50, "half way", force=True)
        if FakeDriver.outcome == "handoff":
            raise Handoff("Opened in Studio")
        if FakeDriver.outcome == "fail":
            raise RuntimeError("nozzle clog")
        return "made it"


@pytest.mark.parametrize("outcome,run_state,job", [
    ("done", "done", "done"), ("handoff", "running", "running"), ("fail", "failed", "failed"),
])
def test_agent_runs_jobs(app, client, tmp_path, cube_stl, monkeypatch, outcome, run_state, job):
    from pyslate.shop_agent import agent as agent_mod

    monkeypatch.setitem(agent_mod.DRIVERS, "fake", FakeDriver)
    FakeDriver.outcome, FakeDriver.seen = outcome, []
    _, (job_id,) = paid_order(app, cube_stl)
    client.post(f"/admin/job/{job_id}/send", data={"machine_id": "bambu", "copies": "1"})
    a = Agent({"machines": [{"id": "bambu", "driver": "fake"}, {"id": "x1", "driver": "fake", "enabled": False}]},
              api=ClientApi(client), workdir=tmp_path / "work")
    assert list(a.drivers) == ["bambu"]
    assert a.tick(wait=True) == 1
    assert FakeDriver.seen[0][0] == "bambu" and len(FakeDriver.seen[0][1]) == 5
    with app.state.session_factory() as db:
        run = db.query(JobRun).one()
        assert run.state == run_state and run.agent == "yaeger"
    assert job_state(app, job_id)[0] == job
    assert a.tick(wait=True) == 0  # nothing left


class FakeSerial:
    """A Marlin printer on a serial port that asks for one resend."""

    def __init__(self):
        self.sent, self.replies, self.asked = [], [], False

    def write(self, data):
        line = data.decode().strip()
        self.sent.append(line)
        if line.startswith("N2 ") and not self.asked:
            self.asked = True
            self.replies += [b"Resend: 2\n", b"ok\n"]
        elif line.startswith("N"):
            self.replies.append(b"ok\n")

    def readline(self):
        return self.replies.pop(0) if self.replies else b""


class Ctx:
    def __init__(self, cancel_after=None):
        self.n, self.cancel_after = 0, cancel_after

    def progress(self, *a, **k):
        pass

    def cancelled(self):
        self.n += 1
        return self.cancel_after is not None and self.n > self.cancel_after


def test_marlin_streams_with_checksums_and_resends(tmp_path):
    lines = clean_lines("; header\nG28 ; home\nG1 X10\n\nG1 X20\n")
    assert lines == ["G28", "G1 X10", "G1 X20"]
    d = MarlinDriver({"id": "a8s", "port": "COM4"}, tmp_path)
    port = FakeSerial()
    d.stream(port, lines, Ctx())
    body = [s.split("*")[0] for s in port.sent]
    assert body == ["N0 M110 N0", "N1 G28", "N2 G1 X10", "N2 G1 X10", "N3 G1 X20"]
    assert port.sent[1] == f"N1 G28*{checksum('N1 G28')}"


def test_marlin_cancel_stops_heaters(tmp_path):
    d = MarlinDriver({"id": "a8s", "port": "COM4"}, tmp_path)
    port = FakeSerial()
    with pytest.raises(Cancelled):
        d.stream(port, ["G28", "G1 X10", "G1 X20"], Ctx(cancel_after=1))
    assert "M104 S0" in port.sent and "M140 S0" in port.sent


def test_folder_driver_hands_off(tmp_path):
    from pyslate.shop_agent.drivers.folder import FolderDriver

    src = tmp_path / "a.nc"
    src.write_text("G0 X0")
    d = FolderDriver({"id": "24r", "folder": str(tmp_path / "share")}, tmp_path)
    with pytest.raises(Handoff) as h:
        d.run({"settings": {"material": "Birch plywood 18 mm"}}, src, Ctx())
    assert (tmp_path / "share" / "a.nc").exists() and "Birch" in str(h.value)
    assert d.status()["state"] == "manual"


# ---- shop-floor HUD -----------------------------------------------------------------


def test_board_feed_schedules_queues(app, client, cube_stl):
    _, (job_id,) = paid_order(app, cube_stl, quantity=3)
    client.post(f"/admin/job/{job_id}/send", data={"machine_id": "bambu", "copies": "1"})
    _, (job2,) = paid_order(app, cube_stl, quantity=2)
    with app.state.session_factory() as db:
        run_id = db.query(JobRun).one().id
    client.post(f"/api/agent/runs/{run_id}/claim", headers=AGENT)
    client.post(f"/api/agent/runs/{run_id}/update", headers=AGENT, json={"state": "running", "progress": 50})
    feed = client.get("/api/agent/board", headers=AGENT).json()
    assert client.get("/api/agent/board").status_code == 401
    bambu = next(m for m in feed["machines"] if m["id"] == "bambu")
    assert bambu["current"]["progress"] == 50 and bambu["current"]["minutes_left"] > 0
    assert [q["job_id"] for q in bambu["queue"]] == [job2]
    assert bambu["queue"][0]["start"] < bambu["queue"][0]["end"] and not bambu["queue"][0]["late"]
    assert feed["totals"]["running"] == 1 and feed["totals"]["queued"] == 1
    assert {o["order"] for o in feed["orders"]} and client.get("/admin/production/board.json").status_code == 200


@pytest.mark.parametrize("width,height,lines", [(200, 56, None), (150, 40, ["laser"]), (90, 30, None)])
def test_hud_renders_feed(app, client, cube_stl, width, height, lines):
    from rich.console import Console

    from pyslate.shop_agent.hud import demo_feed, render

    paid_order(app, cube_stl)
    for feed in (demo_feed(), client.get("/api/agent/board", headers=AGENT).json()):
        console = Console(record=True, width=width, height=height, file=io.StringIO())
        console.print(render(feed, width, height, lines=lines), height=height)
        text = console.export_text()
        assert "PYSLATE" in text and "SCHEDULE" in text


def test_full_journey_site_order_to_shipped(app, client, plate_stl, cube_stl):
    """An order placed on the site waits for payment on the board, queues, runs, and the
    customer sees each part's progress and journey."""
    from pyslate.models import Order

    cfg = app.state.settings
    with app.state.session_factory() as db:
        quote = Quote()
        db.add(quote)
        for path in (plate_stl, cube_stl):
            services.add_part_to_quote(db, quote, services.store_part(db, cfg.upload_dir, path.name, path))
        db.flush()
        order = services.place_order(db, quote, "c@example.com", "Casey", "2 Main St")
        number, token = order.number, order.access_token
    board = client.get("/admin/production").text
    assert "waiting for payment" in board and f"#{number}" in board
    assert client.get("/api/agent/board", headers=AGENT).json()["awaiting_payment"][0]["order"] == number
    r = client.post(f"/admin/order/{number}/paid", data={"back": "/admin/production"}, follow_redirects=False)
    assert r.headers["location"] == "/admin/production"
    page = client.get(f"/order/{number}?t={token}").text
    assert "In the queue for the" in page
    with app.state.session_factory() as db:
        jobs = db.query(Order).filter_by(number=number).one().jobs
        ids = {j.line: (j.id, j.machine_id) for j in jobs}
    for line, (jid, machine) in ids.items():
        client.post(f"/admin/job/{jid}/send", data={"machine_id": machine, "copies": "1"})
    for run in client.get("/api/agent/runs", headers=AGENT).json()["runs"]:
        client.post(f"/api/agent/runs/{run['id']}/claim", headers=AGENT)
        client.post(f"/api/agent/runs/{run['id']}/update", headers=AGENT, json={"state": "running", "progress": 35})
    page = client.get(f"/order/{number}?t={token}").text
    assert "Cutting on the" in page and "Printing on the" in page and "35%" in page
    assert "plate.stl: cutting on the" in page
    for run in client.get("/admin/production/status.json").json()["active"]:
        client.post(f"/api/agent/runs/{run}/update", headers=AGENT, json={"state": "done"})
    page = client.get(f"/order/{number}?t={token}").text
    assert "Finishing" in page and "cube.stl: made, 1 of 1" in page
    admin = client.get(f"/admin/order/{number}").text
    assert "Machine runs" in admin and "yaeger" in admin


def test_hud_in_the_admin(app, client, cube_stl):
    page = client.get("/admin/hud?line=print").text
    assert "/admin/production/board.json" in page and "SHOP FLOOR" in page
    assert "Terminal view" in client.get("/admin/production").text
    assert TestClient(app).get("/admin/hud", follow_redirects=False).status_code == 303
