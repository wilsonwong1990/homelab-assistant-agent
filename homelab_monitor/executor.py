"""Restricted execution boundary. No LLM output or arbitrary commands accepted."""

from __future__ import annotations

import hashlib
import contextlib
from datetime import datetime
import json
import os
import re
import socket
import socketserver
import sqlite3
import subprocess
import time
import uuid
from pathlib import Path

from .core import ConfigurationError, TransportError, open_db, request_json


class Denied(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def policy_at(path):
    policy = json.loads(Path(path).read_text())
    if policy.get("enabled") is not True:
        raise Denied("execution disabled by policy")
    if not isinstance(policy.get("runbooks"), dict):
        raise Denied("runbooks must be an object")
    for key, book in policy["runbooks"].items():
        if not isinstance(book, dict):
            raise Denied(f"{key}: runbook must be an object")
        if book.get("operation") != "restart_systemd":
            raise Denied(f"{key}: unsupported runbook operation")
        if book.get("lane") not in {"discord", "github"}:
            raise Denied(f"{key}: invalid authorization lane")
        if not re.fullmatch(r"[a-zA-Z0-9_-]+\.service", book.get("unit", "")):
            raise Denied(f"{key}: invalid fixed systemd unit")
        if not isinstance(book.get("check"), str) or not book.get("impact") or not book.get("recovery"):
            raise Denied(f"{key}: check, impact and recovery are required")
        if not isinstance(book.get("version"), str) or not book["version"]:
            raise Denied(f"{key}: explicit runbook version required")
        if book["lane"] == "discord" and book.get("low_risk") is not True:
            raise Denied(f"{key}: Discord requires explicit low-risk classification")
    digest = hashlib.sha256(canonical(policy).encode()).hexdigest()
    return policy, digest


def action_db(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript("""
        PRAGMA journal_mode=WAL;
        PRAGMA busy_timeout=10000;
        CREATE TABLE IF NOT EXISTS actions (
            id TEXT PRIMARY KEY, digest TEXT NOT NULL, payload TEXT NOT NULL,
            created REAL NOT NULL, expires REAL NOT NULL, state TEXT NOT NULL,
            actor TEXT, result TEXT);
    """)
    os.chmod(path, 0o600)
    return db


def validate_incident(observer_path, book, incident, expected_definition=None):
    with contextlib.closing(open_db(observer_path, readonly=True)) as db:
        row = db.execute("SELECT * FROM checks WHERE id=?", (book["check"],)).fetchone()
    if (row is None or row["status"] != "firing" or row["incident"] != incident
            or time.time() - row["updated"] > 180 or row["failures"] < 1
            or row["evidence"] == "suppressed by dependency or maintenance"
            or (expected_definition is not None and row["definition"] != expected_definition)):
        raise Denied("incident is stale, suppressed, resolved, or does not match the runbook")
    return row["definition"]


def gate(policy, kill_path):
    if Path(kill_path).exists():
        raise Denied("execution kill switch is active")
    if not policy.get("runbooks"):
        raise Denied("no approved runbooks")


def propose(db, policy_path, observer_path, kill_path, key, issue=None):
    policy, policy_digest = policy_at(policy_path)
    gate(policy, kill_path)
    book = policy["runbooks"].get(key)
    if book is None:
        raise Denied("unknown runbook; configuration and unknown actions require GitHub review")
    with contextlib.closing(open_db(observer_path, readonly=True)) as observer:
        row = observer.execute("SELECT incident FROM checks WHERE id=?", (book["check"],)).fetchone()
    incident = row["incident"] if row else None
    check_definition = validate_incident(observer_path, book, incident)
    if db.execute("SELECT count(*) FROM actions WHERE state='pending' AND expires>?", (time.time(),)).fetchone()[0] >= 100:
        raise Denied("pending proposal limit reached")
    if book["lane"] == "github" and (type(issue) is not int or issue < 1):
        raise Denied("GitHub runbooks require an issue number")
    payload = {"runbook": key, "definition": book, "incident": incident,
               "policy_digest": policy_digest, "check_definition": check_definition,
               "issue": issue, "nonce": uuid.uuid4().hex}
    encoded = canonical(payload)
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    key = uuid.uuid4().hex
    now = time.time()
    with db:
        db.execute("INSERT INTO actions VALUES(?,?,?,?,?,'pending',NULL,NULL)",
                   (key, digest, encoded, now, now + 300))
    return {"id": key, "digest": digest, "expires": now + 300, "proposal": payload}


def github_actor(policy, proposal, action, comment_id):
    github = policy.get("github", {})
    repository = github.get("repository", "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise Denied("invalid GitHub repository policy")
    if type(comment_id) is not int or comment_id < 1:
        raise Denied("invalid approval comment ID")
    token = os.environ.get("GITHUB_READ_TOKEN")
    if not token:
        raise Denied("GITHUB_READ_TOKEN is missing")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    base = f"https://api.github.com/repos/{repository}"
    comment = request_json(f"{base}/issues/comments/{comment_id}", headers=headers)
    actor = comment.get("user", {})
    expected_issue = f"{base}/issues/{proposal['issue']}"
    expected_body = f"approve {action['id']} {action['digest']}"
    try:
        created = datetime.fromisoformat(comment["created_at"].replace("Z", "+00:00")).timestamp()
    except (KeyError, TypeError, ValueError, AttributeError):
        raise Denied("GitHub comment creation time is invalid") from None
    if (comment.get("issue_url") != expected_issue or comment.get("body", "").strip() != expected_body
            or str(actor.get("id")) not in github.get("allowed_user_ids", [])
            or actor.get("type") != "User"
            or comment.get("created_at") != comment.get("updated_at")
            or created < action["created"] - 1 or created > action["expires"]):
        raise Denied("GitHub approval identity, issue, exact proposal, or original comment did not match")
    issue = request_json(expected_issue, headers=headers)
    if issue.get("state") != "open" or "pull_request" in issue:
        raise Denied("IssueOps approval requires an open issue")
    login = actor.get("login", "")
    if not re.fullmatch(r"[a-zA-Z0-9-]+", login):
        raise Denied("invalid GitHub actor")
    permissions = request_json(f"{base}/collaborators/{login}/permission", headers=headers)
    if permissions.get("permission") not in {"admin", "write", "maintain"}:
        raise Denied("GitHub approver no longer has write permission")
    current = request_json(f"{base}/issues/comments/{comment_id}", headers=headers)
    if not isinstance(current, dict) or any(
            current.get(field) != comment.get(field)
            for field in ("body", "updated_at", "issue_url", "user")):
        raise Denied("GitHub approval changed during verification")
    return f"github:{actor['id']}:comment:{comment_id}"


def discord_actor(policy, context):
    discord = policy.get("discord", {})
    if (set(context) != {"user_id", "guild_id", "channel_id"}
            or not all(isinstance(value, str) and value.isdigit() for value in context.values())
            or context["user_id"] not in discord.get("allowed_user_ids", [])
            or context["guild_id"] != discord.get("guild_id")
            or context["channel_id"] != discord.get("channel_id")):
        raise Denied("Discord user/guild/channel is not authorized")
    return f"discord:{context['user_id']}"


def run_systemd(book):
    # The OS sudoers policy must separately allow only this exact fixed unit.
    command = ["/usr/bin/sudo", "-n", "/usr/bin/systemctl", "restart", book["unit"]]
    try:
        completed = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, timeout=30, check=False)
        if completed.returncode != 0:
            return "failed: restart command returned nonzero; inspect executor journal"
        verified = subprocess.run(
            ["/usr/bin/systemctl", "is-active", "--quiet", book["unit"]],
            stdin=subprocess.DEVNULL, capture_output=True, timeout=10, check=False,
        )
    except subprocess.TimeoutExpired:
        return "unknown: command timed out; inspect actual state before any new action"
    except OSError as error:
        return f"failed: command could not start ({type(error).__name__})"
    return "succeeded: systemd reports active; confirm application recovery in monitoring" if verified.returncode == 0 else "failed: service did not verify active"


def approve(db, policy_path, observer_path, kill_path, key, digest, *, lane, context=None, comment_id=None, runner=run_systemd):
    policy, policy_digest = policy_at(policy_path)
    gate(policy, kill_path)
    action = db.execute("SELECT * FROM actions WHERE id=?", (key,)).fetchone()
    if action is None or action["state"] != "pending" or action["expires"] < time.time():
        raise Denied("proposal is absent, expired, or already consumed")
    payload = json.loads(action["payload"])
    if (digest != action["digest"] or payload["policy_digest"] != policy_digest
            or hashlib.sha256(action["payload"].encode()).hexdigest() != digest
            or payload["definition"] != policy["runbooks"].get(payload["runbook"])):
        raise Denied("proposal or approved policy changed")
    book = payload["definition"]
    if book["lane"] != lane:
        raise Denied("approval cannot change the runbook authorization lane")
    if lane == "discord":
        actor = discord_actor(policy, context or {})
    elif lane == "github":
        actor = github_actor(policy, payload, action, comment_id)
    else:
        raise Denied("unsupported approval lane")
    # Authentication may make network calls. Re-read policy and stop switch last.
    current_policy, current_digest = policy_at(policy_path)
    gate(current_policy, kill_path)
    if current_digest != policy_digest or action["expires"] < time.time():
        raise Denied("policy changed or proposal expired during approval")
    validate_incident(observer_path, book, payload["incident"], payload["check_definition"])
    with db:
        db.execute("BEGIN IMMEDIATE")
        previous = db.execute(
            "SELECT payload,state,created FROM actions WHERE state IN ('executing','unknown') OR (state IN ('succeeded','failed') AND created>?) ORDER BY created DESC",
            (time.time() - 600,),
        ).fetchall()
        for item in previous:
            same_target = json.loads(item["payload"])["definition"]["unit"] == book["unit"]
            if same_target and (item["state"] == "executing" or time.time() - item["created"] < 600
                                or item["state"] == "unknown"):
                raise Denied("target cooldown or uncertain previous execution requires operator review")
        changed = db.execute(
            "UPDATE actions SET state='executing',actor=? WHERE id=? AND state='pending'",
            (actor, key),
        ).rowcount
        if changed != 1:
            raise Denied("proposal already consumed")
    # Persist consumption before the side effect. A crash never auto-replays it.
    result = runner(book)
    state = "succeeded" if result.startswith("succeeded:") else "unknown" if result.startswith("unknown:") else "failed"
    with db:
        db.execute("UPDATE actions SET state=?,result=? WHERE id=?", (state, result, key))
    return {"id": key, "state": state, "result": result}


def rpc(path, message):
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(60)
        client.connect(str(path))
        client.sendall((canonical(message) + "\n").encode())
        with client.makefile("rb") as stream:
            raw = stream.readline(65537)
        if len(raw) > 65536:
            raise Denied("executor response too large")
    response = json.loads(raw)
    if "error" in response:
        raise Denied(response["error"])
    return response["result"]


def serve_executor(socket_path, db_path, policy_path, observer_path, kill_path):
    path = Path(socket_path)
    if path.exists():
        raise ConfigurationError("executor socket exists; verify the old process stopped before removing it")
    path.parent.mkdir(parents=True, exist_ok=True)

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(65)
            try:
                raw = self.rfile.readline(8193)
                if len(raw) > 8192:
                    raise Denied("request exceeds size limit")
                message = json.loads(raw)
                with contextlib.closing(action_db(db_path)) as db:
                    if message["method"] == "propose":
                        result = propose(db, policy_path, observer_path, kill_path,
                                         message["runbook"], message.get("issue"))
                    elif message["method"] == "approve":
                        result = approve(db, policy_path, observer_path, kill_path,
                                         message["id"], message["digest"], lane=message["lane"],
                                         context=message.get("context"), comment_id=message.get("comment_id"))
                    else:
                        raise Denied("unsupported executor method")
                response = {"result": result}
            except (Denied, ConfigurationError, TransportError, ValueError, KeyError, TypeError) as error:
                response = {"error": str(error)}
            except (OSError, sqlite3.Error) as error:
                response = {"error": f"executor unavailable ({type(error).__name__}); no automatic retry"}
            self.wfile.write((canonical(response) + "\n").encode())

    with socketserver.UnixStreamServer(str(path), Handler) as server:
        os.chmod(path, 0o660)
        try:
            server.serve_forever()
        finally:
            path.unlink(missing_ok=True)
