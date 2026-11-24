"""Database tables and the order and job state machines."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return uuid.uuid4().hex


def new_token() -> str:
    return secrets.token_urlsafe(18)


class Base(DeclarativeBase):
    pass


# Order states the customer sees, in order.
ORDER_STATES = [
    "awaiting_payment",
    "paid",
    "in_queue",
    "making",
    "finishing",
    "shipped",
    "delivered",
    "cancelled",
]
ORDER_LABELS = {
    "awaiting_payment": "Awaiting payment",
    "paid": "Paid",
    "in_queue": "In queue",
    "making": "Making",
    "finishing": "Finishing",
    "shipped": "Shipped",
    "delivered": "Delivered",
    "cancelled": "Cancelled",
}

# Machine job states and the moves the shop may make.
# "sent" means a run was handed to the shop agent and the machine has not started yet.
# "running" -> "queued" happens when a run made some, but not all, of the job's copies.
JOB_TRANSITIONS = {
    "queued": {"sent", "running", "review"},
    "review": {"queued"},
    "sent": {"queued", "running", "failed"},
    "running": {"done", "failed", "queued"},
    "failed": {"queued"},
    "done": set(),
}
JOB_LABELS = {
    "queued": "Queued",
    "review": "Needs review",
    "sent": "Sent to machine",
    "running": "Running",
    "failed": "Failed",
    "done": "Done",
}

# A run is one send of a job to a machine. The shop agent on the shop PC claims pending
# runs, starts the machine and reports back. "cancel_requested" asks the agent to stop.
RUN_ACTIVE_STATES = ("pending", "claimed", "running", "cancel_requested")
RUN_FINAL_STATES = ("done", "failed", "cancelled")
RUN_LABELS = {
    "pending": "Waiting for the shop agent",
    "claimed": "Agent preparing",
    "running": "Running",
    "cancel_requested": "Stopping",
    "done": "Done",
    "failed": "Failed",
    "cancelled": "Cancelled",
}


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Part(Base):
    __tablename__ = "parts"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    filename: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(64))
    preview_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    geometry: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Quote(Base):
    __tablename__ = "quotes"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    token: Mapped[str] = mapped_column(String(32), unique=True, index=True, default=new_token)
    lead_tier: Mapped[str] = mapped_column(String(16), default="standard")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    lines: Mapped[list["QuoteLine"]] = relationship(
        back_populates="quote", cascade="all, delete-orphan", order_by="QuoteLine.position"
    )
    order: Mapped["Order | None"] = relationship(back_populates="quote", uselist=False)


class QuoteLine(Base):
    __tablename__ = "quote_lines"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    quote_id: Mapped[str] = mapped_column(ForeignKey("quotes.id"))
    part_id: Mapped[str] = mapped_column(ForeignKey("parts.id"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    material_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    line: Mapped[str] = mapped_column(String(16))  # print, laser, review
    machine_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    route_reason: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    quote: Mapped[Quote] = relationship(back_populates="lines")
    part: Mapped[Part] = relationship()


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    number: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    quote_id: Mapped[str] = mapped_column(ForeignKey("quotes.id"), unique=True)
    access_token: Mapped[str] = mapped_column(String(32), default=new_token)
    email: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    shipping_address: Mapped[str] = mapped_column(Text)
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="awaiting_payment")
    total_cents: Mapped[int] = mapped_column(Integer)
    lead_days: Mapped[int] = mapped_column(Integer)
    stripe_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    tracking: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    quote: Mapped[Quote] = relationship(back_populates="order")
    events: Mapped[list["OrderEvent"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OrderEvent.at"
    )
    jobs: Mapped[list["Job"]] = relationship(back_populates="order", cascade="all, delete-orphan")

    @property
    def status_label(self) -> str:
        return ORDER_LABELS.get(self.status, self.status)


class OrderEvent(Base):
    __tablename__ = "order_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"))
    status: Mapped[str] = mapped_column(String(32))
    note: Mapped[str] = mapped_column(Text, default="")
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    order: Mapped[Order] = relationship(back_populates="events")


class Job(Base):
    """One machine job: a quote line's parts on one machine."""

    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"))
    quote_line_id: Mapped[str] = mapped_column(ForeignKey("quote_lines.id"))
    line: Mapped[str] = mapped_column(String(16))
    machine_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(16), default="queued")
    note: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    order: Mapped[Order] = relationship(back_populates="jobs")
    quote_line: Mapped[QuoteLine] = relationship()
    runs: Mapped[list["JobRun"]] = relationship(order_by="JobRun.created_at", viewonly=True)

    @property
    def label(self) -> str:
        return JOB_LABELS.get(self.state, self.state)

    @property
    def copies_done(self) -> int:
        return sum(r.copies for r in self.runs if r.state == "done")

    @property
    def active_run(self) -> "JobRun | None":
        return next((r for r in reversed(self.runs) if r.state in RUN_ACTIVE_STATES), None)


class ServiceRequest(Base):
    """A request for design or documentation work: system design, blueprints, schematics."""

    __tablename__ = "service_requests"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    number: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    service: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(64), default="")
    description: Mapped[str] = mapped_column(Text)
    budget: Mapped[str] = mapped_column(String(64), default="")
    needed_by: Mapped[str] = mapped_column(String(64), default="")
    files: Mapped[list] = mapped_column(JSON, default=list)  # [{"name": original, "stored": stored name}]
    status: Mapped[str] = mapped_column(String(32), default="new")
    shop_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ---- customer accounts (new tables only, so existing databases upgrade with create_all) ----


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255), default="")
    company: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(64), default="")
    shipping_address: Mapped[str] = mapped_column(Text, default="")
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    session_version: Mapped[int] = mapped_column(Integer, default=1)  # bump to sign out everywhere
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CustomerOrder(Base):
    """Orders a customer placed while signed in, or added with the order's private link."""

    __tablename__ = "customer_orders"
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    order: Mapped[Order] = relationship()


class SavedQuote(Base):
    __tablename__ = "saved_quotes"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    quote_id: Mapped[str] = mapped_column(ForeignKey("quotes.id"))
    name: Mapped[str] = mapped_column(String(255), default="")
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    quote: Mapped[Quote] = relationship()


class SavedDesign(Base):
    """A design-studio drawing the customer saved to come back to."""

    __tablename__ = "saved_designs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    design: Mapped[dict] = mapped_column(JSON)  # the studio's own shapes, machine and material
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ---- production: machine runs and the shop agent (new tables only) ----


class JobRun(Base):
    __tablename__ = "job_runs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    machine_id: Mapped[str] = mapped_column(String(64), index=True)
    copies: Mapped[int] = mapped_column(Integer, default=1)
    state: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    file_kind: Mapped[str] = mapped_column(String(16), default="original")  # original, svg, dxf
    settings: Mapped[dict] = mapped_column(JSON, default=dict)  # power, speed, passes, slicer profile...
    progress: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(Text, default="")
    agent: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    job: Mapped[Job] = relationship()

    @property
    def label(self) -> str:
        return RUN_LABELS.get(self.state, self.state)


class MachineStatus(Base):
    """What the shop agent last reported about one machine."""

    __tablename__ = "machine_status"
    machine_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    state: Mapped[str] = mapped_column(String(20), default="unknown")  # idle, busy, paused, error, offline, manual
    detail: Mapped[str] = mapped_column(Text, default="")
    progress: Mapped[int | None] = mapped_column(Integer, nullable=True)
    driver: Mapped[str] = mapped_column(String(32), default="")
    agent: Mapped[str] = mapped_column(String(64), default="")
    seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


def make_session_factory(url: str):
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
