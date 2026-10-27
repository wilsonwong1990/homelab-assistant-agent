"""Deterministic checks, durable incidents, and model-independent delivery."""

from __future__ import annotations

import json
import hashlib
import http.client
import logging
import math
import os
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

LOG = logging.getLogger(__name__)
MAX_BODY = 2 * 1024 * 1024
KINDS = {"http", "proxmox", "unifi", "home_assistant"}
ID = re.compile(r"[a-zA-Z0-9_-]{1,80}\Z")


class ConfigurationError(ValueError):
    pass


class TransportError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise TransportError("HTTP redirects are not allowed")


def request_json(url, *, headers=None, body=None, timeout=10, expect_json=True):
    """Never forward credentials to a redirect or expose remote error bodies."""
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json", **(headers or {})}
    )
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect).open(request, timeout=timeout) as response:
            raw = response.read(MAX_BODY + 1)
            if len(raw) > MAX_BODY:
                raise TransportError("response exceeds size limit")
            return json.loads(raw) if raw and expect_json else None
    except urllib.error.HTTPError as error:
        raise TransportError(f"HTTP {error.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as error:
        raise TransportError(f"network/TLS failure ({type(error).__name__})") from None
    except (ValueError, UnicodeError):
        raise TransportError("invalid JSON response") from None


def positive(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ConfigurationError(f"{name} must be a positive number")


def load_config(path):
    config = json.loads(Path(path).read_text())
    if not isinstance(config, dict):
        raise ConfigurationError("configuration must be an object")
    checks = config.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ConfigurationError("checks must be a nonempty list")
    seen = set()
    if len(checks) > 256:
        raise ConfigurationError("at most 256 checks per monitor instance")
    for check in checks:
        if not isinstance(check, dict):
            raise ConfigurationError("checks must contain objects")
        key = check.get("id", "")
        if not isinstance(key, str) or not ID.fullmatch(key) or key in seen:
            raise ConfigurationError("check IDs must be unique, safe identifiers")
        seen.add(key)
        if check.get("kind") not in KINDS:
            raise ConfigurationError(f"{key}: unsupported check kind")
        if not isinstance(check.get("url"), str):
            raise ConfigurationError(f"{key}: URL must be a string")
        url = urllib.parse.urlsplit(check["url"])
        if url.scheme not in {"https", "http"} or not url.hostname or url.username or url.password:
            raise ConfigurationError(f"{key}: invalid URL")
        if url.query or url.fragment:
            raise ConfigurationError(f"{key}: put credentials in environment headers, not URLs")
        if url.scheme != "https" and url.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ConfigurationError(f"{key}: remote checks require HTTPS")
        for field in ("failures", "recoveries"):
            value = check.get(field, 2)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ConfigurationError(f"{key}: {field} must be a positive integer")
        positive(check.get("timeout", 10), f"{key}.timeout")
        if check.get("timeout", 10) > 30:
            raise ConfigurationError(f"{key}: timeout must not exceed 30 seconds")
        if check.get("severity", "warning") not in {"warning", "critical"}:
            raise ConfigurationError(f"{key}: severity must be warning or critical")
        if check.get("kind") in {"proxmox", "unifi"}:
            targets = check.get("expected_online")
            if not isinstance(targets, list) or not targets or not all(isinstance(t, str) for t in targets):
                raise ConfigurationError(f"{key}: expected_online must explicitly name targets")
        if check.get("kind") == "home_assistant" and not check.get("entity"):
            raise ConfigurationError(f"{key}: entity is required (use http for HA health)")
        if "expected_states" in check and (
                not isinstance(check["expected_states"], list) or not check["expected_states"]
                or not all(isinstance(state, str) for state in check["expected_states"])):
            raise ConfigurationError(f"{key}: expected_states must be a nonempty string list")
        if not isinstance(check.get("headers_env", {}), dict) or not all(
                isinstance(name, str) and isinstance(env, str)
                for name, env in check.get("headers_env", {}).items()):
            raise ConfigurationError(f"{key}: headers_env must map header names to environment names")
        maintenance = check.get("maintenance_until", 0)
        if isinstance(maintenance, bool) or not isinstance(maintenance, (int, float)) or not math.isfinite(maintenance):
            raise ConfigurationError(f"{key}: maintenance_until must be a Unix timestamp")
    for check in checks:
        if not isinstance(check.get("depends_on", []), list) or not all(
                isinstance(dep, str) for dep in check.get("depends_on", [])):
            raise ConfigurationError(f"{check['id']}: depends_on must be a string list")
        if any(dep not in seen or dep == check["id"] for dep in check.get("depends_on", [])):
            raise ConfigurationError(f"{check['id']}: invalid dependency")
    ordered, visiting = [], set()

    def visit(check):
        if check["id"] in visiting:
            raise ConfigurationError("cyclic check dependencies")
        if check in ordered:
            return
        visiting.add(check["id"])
        for dep in check.get("depends_on", []):
            visit(next(c for c in checks if c["id"] == dep))
        visiting.remove(check["id"])
        ordered.append(check)

    for check in checks:
        visit(check)
    config["checks"] = ordered
    positive(config.get("interval", 60), "interval")
    positive(config.get("retention_days", 30), "retention_days")
    return config


def open_db(path, readonly=False):
    if readonly:
        connection = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    else:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
        connection.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS checks (
                id TEXT PRIMARY KEY, status TEXT NOT NULL, failures INTEGER NOT NULL,
                successes INTEGER NOT NULL, incident TEXT, updated REAL NOT NULL,
                evidence TEXT NOT NULL, severity TEXT NOT NULL, definition TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY, check_id TEXT NOT NULL, incident TEXT NOT NULL,
                kind TEXT NOT NULL, text TEXT NOT NULL, created REAL NOT NULL,
                sent REAL, attempts INTEGER NOT NULL DEFAULT 0, retry_at REAL NOT NULL DEFAULT 0,
                investigated INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS investigations (
                event_id TEXT PRIMARY KEY, state TEXT NOT NULL, result TEXT, updated REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS heartbeat (id INTEGER PRIMARY KEY CHECK(id=1), updated REAL);
        """)
        os.chmod(path, 0o640)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout=10000")
    return connection


def headers_for(check):
    headers = {}
    for name, env in check.get("headers_env", {}).items():
        value = os.environ.get(env)
        if not value:
            raise ConfigurationError(f"{check['id']}: missing environment variable {env}")
        headers[name] = value
    return headers


def collect(check):
    """Return bounded, nonsecret evidence instead of raw device/log responses."""
    kind = check["kind"]
    data = request_json(check["url"], headers=headers_for(check),
                        timeout=check.get("timeout", 10), expect_json=kind != "http")
    if kind == "http":
        return True, "HTTP endpoint responded successfully"
    if kind == "home_assistant":
        if not isinstance(data, dict) or data.get("entity_id") != check["entity"]:
            raise TransportError("HA entity response does not match configured entity")
        state = data.get("state")
        if not isinstance(state, str):
            raise TransportError("HA entity state missing")
        healthy = state not in {"unavailable", "unknown"}
        if "expected_states" in check:
            healthy = state in check["expected_states"]
        return healthy, "HA entity available" if healthy else "HA entity unavailable or unexpected state"
    rows = data.get("data") if isinstance(data, dict) else None
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise TransportError("inventory response must contain a data list")
    if kind == "proxmox":
        if not all(isinstance(row.get("node"), str) and isinstance(row.get("status"), str) for row in rows):
            raise TransportError("invalid Proxmox node inventory")
        states = {row.get("node"): row.get("status") == "online" for row in rows}
    else:
        # A partial inventory must not silently classify absent devices as down.
        total = data.get("totalCount", len(rows))
        if type(total) is not int or total < len(rows):
            raise TransportError("invalid UniFi inventory count")
        for _ in range(20):
            if len(rows) >= total:
                break
            page = request_json(
                check["url"] + f"?offset={len(rows)}&limit=100",
                headers=headers_for(check), timeout=check.get("timeout", 10),
            )
            extra = page.get("data") if isinstance(page, dict) else None
            if (not isinstance(extra, list) or not extra
                    or not all(isinstance(row, dict) for row in extra)
                    or page.get("totalCount") != total):
                raise TransportError("incomplete or changing UniFi inventory")
            rows.extend(extra)
        if len(rows) != total:
            raise TransportError("UniFi inventory exceeds bounded pagination")
        if not all(isinstance(row.get("id", row.get("mac")), str) for row in rows):
            raise TransportError("invalid UniFi device identity")
        # UniFi integration API uses id/state; legacy API uses mac/state=1.
        states = {
            row.get("id", row.get("mac")): row.get("state") in (1, "ONLINE")
            for row in rows
        }
    missing = sum(not states.get(target, False) for target in check["expected_online"])
    return missing == 0, f"{missing}/{len(check['expected_online'])} expected targets offline or absent"


def record(db, check, healthy, evidence, *, now=None, suppressed=False):
    now = time.time() if now is None else now
    old = db.execute("SELECT * FROM checks WHERE id=?", (check["id"],)).fetchone()
    definition = hashlib.sha256(json.dumps(check, sort_keys=True).encode()).hexdigest()
    if old and old["definition"] != definition:
        old = None
    status = old["status"] if old else "healthy"
    incident = old["incident"] if old else None
    failures = 0 if healthy or suppressed else (old["failures"] if old else 0) + 1
    successes = (old["successes"] if old else 0) + 1 if healthy and not suppressed else 0
    event = None
    if suppressed and status != "firing":
        status = "suppressed"
    elif not suppressed and not healthy and status != "firing":
        status = "pending"
        if failures >= check.get("failures", 2):
            status, incident, event = "firing", uuid.uuid4().hex, "firing"
    elif not suppressed and healthy and status == "firing" and successes >= check.get("recoveries", 2):
        status, event = "healthy", "resolved"
    elif not suppressed and healthy and status != "firing":
        status = "healthy"
    severity = check.get("severity", "warning")
    with db:
        db.execute(
            "INSERT OR REPLACE INTO checks VALUES (?,?,?,?,?,?,?,?,?)",
            (check["id"], status, failures, successes, incident, now, evidence, severity, definition),
        )
        if event:
            text = f"[{severity.upper()}] {check['id']} {event}; incident {incident}. {evidence}"
            db.execute(
                "INSERT INTO events(id,check_id,incident,kind,text,created) VALUES (?,?,?,?,?,?)",
                (uuid.uuid4().hex, check["id"], incident, event, text, now),
            )
    return not healthy or suppressed


def poll(config, db):
    unhealthy = set()
    for check in config["checks"]:
        suppressed = any(dep in unhealthy for dep in check.get("depends_on", []))
        suppressed = suppressed or check.get("maintenance_until", 0) > time.time()
        if suppressed:
            healthy, evidence = False, "suppressed by dependency or maintenance"
        else:
            try:
                healthy, evidence = collect(check)
            except (TransportError, ConfigurationError) as error:
                healthy, evidence = False, str(error)
                LOG.warning("check %s: %s", check["id"], error)
        if record(db, check, healthy, evidence, suppressed=suppressed):
            unhealthy.add(check["id"])
    with db:
        db.execute("INSERT OR REPLACE INTO heartbeat VALUES(1,?)", (time.time(),))
        cutoff = time.time() - config.get("retention_days", 30) * 86400
        db.execute("DELETE FROM investigations WHERE event_id IN (SELECT id FROM events WHERE sent IS NOT NULL AND created<?)", (cutoff,))
        db.execute("DELETE FROM events WHERE sent IS NOT NULL AND created<?", (cutoff,))
        for check in db.execute("SELECT id FROM checks").fetchall():
            if check["id"] not in {c["id"] for c in config["checks"]}:
                db.execute("DELETE FROM checks WHERE id=?", (check["id"],))


def discord_url(value):
    parsed = urllib.parse.urlsplit(value)
    if (parsed.scheme != "https" or parsed.hostname != "discord.com"
            or parsed.port not in (None, 443) or parsed.username or parsed.password
            or not re.fullmatch(r"/api/webhooks/\d+/[A-Za-z0-9._-]+", parsed.path)
            or parsed.query or parsed.fragment):
        raise ConfigurationError("Discord webhook must be a canonical discord.com HTTPS webhook")
    return value + "?wait=true"


def deliver(db, webhook):
    url = discord_url(webhook)
    events = db.execute(
        """SELECT event.* FROM events AS event
           WHERE event.sent IS NULL AND event.retry_at<=?
             AND NOT EXISTS (
                 SELECT 1 FROM events AS earlier
                 WHERE earlier.check_id=event.check_id AND earlier.sent IS NULL
                   AND (earlier.created<event.created
                        OR (earlier.created=event.created AND earlier.rowid<event.rowid))
             )
           ORDER BY event.created, event.rowid LIMIT 20""",
        (time.time(),),
    ).fetchall()
    for event in events:
        try:
            request_json(url, body={"content": event["text"][:1900], "allowed_mentions": {"parse": []}})
        except TransportError as error:
            LOG.error("Discord delivery failed for %s: %s", event["id"], error)
            with db:
                attempts = event["attempts"] + 1
                db.execute("UPDATE events SET attempts=?,retry_at=? WHERE id=?",
                           (attempts, time.time() + min(3600, 5 * 2 ** min(attempts, 10)), event["id"]))
        else:
            with db:
                db.execute("UPDATE events SET sent=? WHERE id=?", (time.time(), event["id"]))


def snapshot(db):
    return [dict(row) for row in db.execute("SELECT * FROM checks ORDER BY id")]
