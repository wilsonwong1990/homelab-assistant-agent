import contextlib
import asyncio
from datetime import datetime, timezone
import io
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from homelab_monitor import core, discord_bot, executor, investigation, mcp
from homelab_monitor.cli import main


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db_path = self.root / "monitor.db"
        self.db = core.open_db(self.db_path)
        self.addCleanup(self.db.close)
        self.check = {"id": "app", "kind": "http", "url": "http://127.0.0.1/health",
                      "failures": 1, "recoveries": 1}

    def config(self, checks=None):
        path = self.root / "config.json"
        path.write_text(json.dumps({"checks": checks or [self.check]}))
        return core.load_config(path)


class MonitoringTests(Fixture):
    def test_examples_validate(self):
        config = core.load_config("examples/monitoring/monitoring.example.json")
        self.assertEqual(len(config["checks"]), 4)
        investigation.model_settings(config)

    def test_reject_credentials_and_remote_plaintext(self):
        for url in ("http://remote/health", "https://user:secret@remote/", "https://remote/?token=secret"):
            with self.subTest(url=url), self.assertRaises(core.ConfigurationError):
                self.config([{**self.check, "url": url}])

    def test_dependencies_topological_and_cycles_rejected(self):
        parent = {**self.check, "id": "parent"}
        child = {**self.check, "depends_on": ["parent"]}
        self.assertEqual([c["id"] for c in self.config([child, parent])["checks"]], ["parent", "app"])
        parent["depends_on"] = ["app"]
        with self.assertRaises(core.ConfigurationError):
            self.config([child, parent])

    def test_failure_dedup_recovery_and_restart(self):
        core.record(self.db, self.check, False, "offline")
        incident = core.snapshot(self.db)[0]["incident"]
        core.record(self.db, self.check, False, "offline")
        self.assertEqual(self.db.execute("SELECT count(*) FROM events").fetchone()[0], 1)
        with core.open_db(self.db_path) as reopened:
            core.record(reopened, self.check, True, "online")
        events = self.db.execute("SELECT * FROM events ORDER BY created").fetchall()
        self.assertEqual([e["kind"] for e in events], ["firing", "resolved"])
        self.assertTrue(all(e["incident"] == incident for e in events))

    def test_thresholds_flapping_and_maintenance(self):
        self.check.update(failures=2, recoveries=2)
        core.record(self.db, self.check, False, "offline")
        self.assertEqual(core.snapshot(self.db)[0]["status"], "pending")
        core.record(self.db, self.check, True, "online")
        core.record(self.db, self.check, False, "offline")
        self.assertEqual(self.db.execute("SELECT count(*) FROM events").fetchone()[0], 0)
        core.record(self.db, self.check, False, "offline", suppressed=True)
        core.record(self.db, self.check, False, "offline")
        self.assertEqual(self.db.execute("SELECT count(*) FROM events").fetchone()[0], 0)

    def test_source_failure_suppresses_children(self):
        parent = {**self.check, "id": "parent"}
        config = self.config([{**self.check, "depends_on": ["parent"]}, parent])
        with patch.object(core, "collect", return_value=(False, "unreachable")) as collect:
            core.poll(config, self.db)
        self.assertEqual(collect.call_count, 1)
        self.assertEqual(self.db.execute("SELECT check_id FROM events").fetchone()[0], "parent")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--db", str(self.db_path), "heartbeat"]), 0)

    def test_discord_retry_and_mentions_disabled(self):
        core.record(self.db, self.check, False, "offline")
        webhook = "https://discord.com/api/webhooks/123/abc"
        with patch.object(core, "request_json", side_effect=core.TransportError("HTTP 429")):
            core.deliver(self.db, webhook)
        event = self.db.execute("SELECT * FROM events").fetchone()
        self.assertIsNone(event["sent"])
        self.assertEqual(event["attempts"], 1)
        self.db.execute("UPDATE events SET retry_at=0")
        self.db.commit()
        with patch.object(core, "request_json") as request:
            core.deliver(self.db, webhook)
        self.assertEqual(request.call_args.kwargs["body"]["allowed_mentions"], {"parse": []})
        self.assertIsNotNone(self.db.execute("SELECT sent FROM events").fetchone()[0])

    def test_collectors_expected_targets_only(self):
        with patch.object(core, "request_json", return_value={"data": [
            {"node": "active", "status": "online"}, {"node": "retired", "status": "offline"}]}):
            healthy, _ = core.collect({**self.check, "kind": "proxmox", "expected_online": ["active"]})
        self.assertTrue(healthy)
        entity = {**self.check, "kind": "home_assistant", "entity": "sensor.battery"}
        with patch.object(core, "request_json", return_value={"entity_id": "sensor.battery", "state": "unavailable"}):
            self.assertFalse(core.collect(entity)[0])
        with patch.object(core, "request_json", return_value={"entity_id": "sensor.battery", "state": "80"}):
            self.assertTrue(core.collect(entity)[0])

    def test_unifi_pagination(self):
        with patch.object(core, "request_json", side_effect=[
            {"data": [{"id": "one", "state": "ONLINE"}], "totalCount": 2},
            {"data": [{"id": "two", "state": "ONLINE"}], "totalCount": 2},
        ]) as request:
            self.assertTrue(core.collect({**self.check, "kind": "unifi", "expected_online": ["two"]})[0])
        self.assertIn("?offset=1&limit=100", request.call_args.args[0])

    def test_network_redirection_and_error_redaction(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/redirect":
                    self.send_response(302)
                    self.send_header("Location", "/secret")
                    self.end_headers()
                elif self.path == "/bad":
                    self.send_response(403)
                    self.end_headers()
                    self.wfile.write(b"token=secret")
                else:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"<html>healthy</html>")

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f"http://127.0.0.1:{server.server_port}"
        self.assertTrue(core.collect({**self.check, "url": base})[0])
        with self.assertRaisesRegex(core.TransportError, "redirects"):
            core.request_json(base + "/redirect")
        with self.assertRaisesRegex(core.TransportError, r"^HTTP 403$"):
            core.request_json(base + "/bad")

    def test_local_model_only_and_invalid_output(self):
        for url in ("https://api.openai.com", "http://localhost:11434", "http://127.0.0.1@evil/"):
            with self.assertRaises(core.ConfigurationError):
                investigation.model_settings({"model": {"url": url, "name": "local"}})
        config = {"model": {"name": "local"}}
        with patch.object(investigation, "request_json", side_effect=[
                {"model_info": {"general.architecture": "local"}},
                {"message": {"content": '{"command":"reboot"}'}}]):
            with self.assertRaises(core.TransportError):
                investigation.diagnose(config, {})

    def test_model_failure_never_blocks_alert_and_is_not_replayed(self):
        core.record(self.db, self.check, False, "offline")
        with patch.object(investigation, "diagnose", side_effect=core.TransportError("model offline")):
            self.assertTrue(investigation.investigate_next({}, self.db))
        self.assertFalse(investigation.investigate_next({}, self.db))
        self.assertEqual(self.db.execute("SELECT state FROM investigations").fetchone()[0], "failed")
        with patch.object(core, "request_json") as request:
            core.deliver(self.db, "https://discord.com/api/webhooks/123/abc")
        self.assertEqual(request.call_count, 2)

    def test_mcp_and_readonly_database(self):
        core.record(self.db, self.check, False, "offline")
        with core.open_db(self.db_path, readonly=True) as db:
            with self.assertRaises(sqlite3.OperationalError):
                db.execute("DELETE FROM checks")
            result = mcp.handle(db, {"id": 1, "method": "tools/call",
                                    "params": {"name": "homelab_status", "arguments": {}}})
            self.assertIn("firing", result["result"]["content"][0]["text"])
            result = mcp.handle(db, {"id": 2, "method": "tools/call",
                                    "params": {"name": "restart", "arguments": {}}})
            self.assertIn("error", result)


class ExecutionTests(Fixture):
    def setUp(self):
        super().setUp()
        core.record(self.db, self.check, False, "offline")
        self.policy_path = self.root / "policy.json"
        self.kill = self.root / "STOP"
        self.actions = executor.action_db(self.root / "actions.db")
        self.addCleanup(self.actions.close)
        self.book = {"operation": "restart_systemd", "lane": "discord", "low_risk": True,
                     "unit": "noncritical.service", "check": "app", "version": "1",
                     "impact": "Brief outage of a noncritical app", "recovery": "Inspect journal"}
        self.policy = {"enabled": True, "runbooks": {"restart-app": self.book},
                       "discord": {"allowed_user_ids": ["1"], "guild_id": "2", "channel_id": "3"},
                       "github": {"repository": "owner/infra", "allowed_user_ids": ["42"]}}
        self.context = {"user_id": "1", "guild_id": "2", "channel_id": "3"}
        self.write_policy()
        self.runner = unittest.mock.Mock(return_value="succeeded: verified")

    def write_policy(self):
        self.policy_path.write_text(json.dumps(self.policy))

    def propose(self, issue=None):
        return executor.propose(self.actions, self.policy_path, self.db_path,
                                self.kill, "restart-app", issue)

    def approve(self, action, **kwargs):
        return executor.approve(
            self.actions, self.policy_path, self.db_path, self.kill,
            action["id"], action["digest"], runner=self.runner,
            **({"lane": "discord", "context": self.context} | kwargs),
        )

    def test_disabled_default_and_unknown_actions(self):
        self.policy["enabled"] = False
        self.write_policy()
        with self.assertRaises(executor.Denied):
            self.propose()
        self.policy["enabled"] = True
        self.write_policy()
        with self.assertRaises(executor.Denied):
            executor.propose(self.actions, self.policy_path, self.db_path, self.kill, "reboot")

    def test_exact_approval_consumed_once_and_audited(self):
        action = self.propose()
        self.assertEqual(self.approve(action)["state"], "succeeded")
        with self.assertRaises(executor.Denied):
            self.approve(action)
        self.runner.assert_called_once_with(self.book)
        self.assertEqual(self.actions.execute("SELECT actor FROM actions").fetchone()[0], "discord:1")

    def test_wrong_identity_and_changed_digest(self):
        action = self.propose()
        for field in self.context:
            with self.subTest(field=field), self.assertRaises(executor.Denied):
                self.approve(action, context={**self.context, field: "999"})
        with self.assertRaises(executor.Denied):
            self.approve({**action, "digest": "wrong"})
        self.runner.assert_not_called()

    def test_changed_policy_expiry_and_kill_switch(self):
        action = self.propose()
        self.policy["runbooks"]["restart-app"]["version"] = "2"
        self.write_policy()
        with self.assertRaises(executor.Denied):
            self.approve(action)
        action = self.propose()
        self.actions.execute("UPDATE actions SET expires=0")
        self.actions.commit()
        with self.assertRaises(executor.Denied):
            self.approve(action)
        action = self.propose()
        self.kill.touch()
        with self.assertRaises(executor.Denied):
            self.approve(action)
        self.runner.assert_not_called()

    def test_resolved_or_stale_incident_rejected(self):
        action = self.propose()
        core.record(self.db, self.check, True, "healthy")
        with self.assertRaises(executor.Denied):
            self.approve(action)
        core.record(self.db, self.check, False, "offline")
        action = self.propose()
        self.db.execute("UPDATE checks SET updated=0")
        self.db.commit()
        with self.assertRaises(executor.Denied):
            self.approve(action)

    def test_changed_check_target_invalidates_proposal(self):
        action = self.propose()
        core.record(self.db, {**self.check, "url": "http://127.0.0.1/other-app"}, False, "offline")
        with self.assertRaises(executor.Denied):
            self.approve(action)
        self.runner.assert_not_called()

    def test_unknown_execution_blocks_fresh_proposals(self):
        action = self.propose()
        self.runner.return_value = "unknown: timeout"
        self.assertEqual(self.approve(action)["state"], "unknown")
        with self.assertRaises(executor.Denied):
            self.approve(self.propose())
        self.assertEqual(self.runner.call_count, 1)

    def test_discord_cannot_approve_github_lane(self):
        self.book["lane"] = "github"
        self.write_policy()
        action = self.propose(issue=7)
        with self.assertRaises(executor.Denied):
            self.approve(action)
        self.runner.assert_not_called()

    def test_github_validates_identity_issue_digest_and_permissions(self):
        self.book["lane"] = "github"
        self.write_policy()
        action = self.propose(issue=7)
        stamp = datetime.now(timezone.utc).isoformat()
        comment = {"user": {"id": 42, "type": "User", "login": "owner"},
                   "issue_url": "https://api.github.com/repos/owner/infra/issues/7",
                   "body": f"approve {action['id']} {action['digest']}",
                   "created_at": stamp, "updated_at": stamp}
        with patch.dict(os.environ, {"GITHUB_READ_TOKEN": "test-not-a-real-token"}):
            with patch.object(executor, "request_json", side_effect=[comment, {"state": "open"}, {"permission": "read"}]):
                with self.assertRaises(executor.Denied):
                    self.approve(action, lane="github", comment_id=5)
            with patch.object(executor, "request_json", side_effect=[comment, {"state": "open"}, {"permission": "admin"}, comment]):
                self.assertEqual(self.approve(action, lane="github", comment_id=5)["state"], "succeeded")
        self.runner.assert_called_once()

    def test_no_arbitrary_command_or_unit_injection(self):
        self.book["unit"] = "app.service;reboot"
        self.write_policy()
        with self.assertRaises(executor.Denied):
            self.propose()
        self.runner.assert_not_called()

    def test_consumption_survives_reopen(self):
        action = self.propose()
        self.approve(action)
        with executor.action_db(self.root / "actions.db") as reopened:
            with self.assertRaises(executor.Denied):
                executor.approve(reopened, self.policy_path, self.db_path, self.kill,
                                 action["id"], action["digest"], lane="discord",
                                 context=self.context, runner=self.runner)
        self.runner.assert_called_once()

    def test_policy_change_during_authentication_denied(self):
        self.book["lane"] = "github"
        self.write_policy()
        action = self.propose(issue=7)

        def changed(*args):
            self.book["version"] = "2"
            self.write_policy()
            return "github:42"

        with patch.object(executor, "github_actor", side_effect=changed):
            with self.assertRaises(executor.Denied):
                self.approve(action, lane="github", comment_id=5)
        self.runner.assert_not_called()

    def test_unix_executor_transport_separate_process(self):
        path = self.root / "executor.sock"
        process = subprocess.Popen(
            [sys.executable, "-m", "homelab_monitor", "--db", str(self.db_path),
             "--socket", str(path), "executor", "--policy", str(self.policy_path),
             "--action-db", str(self.root / "transport.db"), "--kill-switch", str(self.kill)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        try:
            deadline = time.monotonic() + 5
            while not path.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(path.exists(), "executor did not bind its socket")
            action = executor.rpc(path, {"method": "propose", "runbook": "restart-app"})
            self.assertEqual(action["proposal"]["definition"]["unit"], "noncritical.service")
            # Exercise the real transport but never allow a real side effect.
            with self.assertRaises(executor.Denied):
                executor.rpc(path, {"method": "approve", "id": action["id"],
                                   "digest": action["digest"], "lane": "discord",
                                   "context": {**self.context, "user_id": "999"}})
        finally:
            process.terminate()
            process.communicate(timeout=5)


class AnalysisTests(Fixture):
    def test_valid_local_analysis_is_bounded_and_uses_canonical_skill(self):
        result = {"summary": "The check failed.", "uncertainty": "Cause not established.",
                  "next_read": "Check application health.", "suggested_fix": "Propose a restart only with required approval."}
        with patch.object(investigation, "request_json", side_effect=[
                {"model_info": {"general.architecture": "local"}},
                {"message": {"content": json.dumps(result)}}]) as request:
            actual = investigation.diagnose({"model": {"name": "local"}}, {"kind": "http"})
        self.assertEqual(actual, result)
        self.assertEqual(request.call_args.args[0], "http://127.0.0.1:11434/api/chat")
        self.assertEqual(request.call_args.kwargs["body"]["options"]["num_ctx"], 4096)
        self.assertIn("Homelab monitoring", request.call_args.kwargs["body"]["messages"][1]["content"])

    def test_cloud_alias_rejected_before_evidence_leaves_worker(self):
        with patch.object(investigation, "request_json", return_value={
                "model_info": {}, "remote_host": "https://ollama.com",
                "remote_model": "cloud-model"}) as request:
            with self.assertRaises(core.TransportError):
                investigation.diagnose({"model": {"name": "local-looking-alias"}}, {"secret_evidence": "not transmitted"})
        self.assertEqual(request.call_count, 1)
        self.assertEqual(request.call_args.kwargs["body"], {"model": "local-looking-alias"})

    def test_manual_queue_limits_and_freshness_display(self):
        core.record(self.db, self.check, True, "healthy")
        investigation.queue_read(self.db, "app")
        with self.assertRaises(core.ConfigurationError):
            investigation.queue_read(self.db, "app")
        with self.assertRaises(core.ConfigurationError):
            investigation.queue_read(self.db, "absent")

    def test_mcp_stdio_roundtrip_has_no_write_surface(self):
        core.record(self.db, self.check, False, "offline")
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2025-03-26"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "homelab_incidents", "arguments": {}}},
        ]
        completed = subprocess.run(
            [sys.executable, "-m", "homelab_monitor", "--db", str(self.db_path), "mcp"],
            input="\n".join(map(json.dumps, requests)) + "\n", text=True,
            capture_output=True, timeout=5, check=True,
        )
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual(len(responses), 3)
        self.assertTrue(all(tool["annotations"]["readOnlyHint"] for tool in responses[1]["result"]["tools"]))
        self.assertIn("firing", responses[2]["result"]["content"][0]["text"])


class DiscordTransportTests(Fixture):
    def invoke(self, content, user=1, guild=2, channel=3, webhook=None, bot=False):
        settings = self.root / "discord.json"
        settings.write_text(json.dumps({"allowed_user_ids": ["1"], "guild_id": "2", "channel_id": "3"}))
        send = AsyncMock()
        message = types.SimpleNamespace(
            content=content, author=types.SimpleNamespace(id=user, bot=bot),
            guild=types.SimpleNamespace(id=guild) if guild else None,
            channel=types.SimpleNamespace(id=channel, send=send), webhook_id=webhook,
        )

        class Client:
            def __init__(self, **kwargs):
                self.options = kwargs

            def event(self, function):
                setattr(self, function.__name__, function)
                return function

            def run(self, *args, **kwargs):
                asyncio.run(self.on_message(message))

        module = types.SimpleNamespace(
            Client=Client, Intents=types.SimpleNamespace(default=lambda: types.SimpleNamespace()),
            AllowedMentions=types.SimpleNamespace(none=lambda: "disabled"),
        )
        with patch.dict(sys.modules, {"discord": module}), patch.dict(os.environ, {"DISCORD_BOT_TOKEN": "fixture"}):
            discord_bot.run_bot(settings, self.db_path, self.root / "socket")
        return send

    def test_gateway_identity_is_passed_not_message_claims(self):
        with patch.object(discord_bot, "rpc", return_value={"state": "succeeded"}) as rpc:
            send = self.invoke("!approve proposal digest")
        self.assertEqual(rpc.call_args.args[1]["context"], {"user_id": "1", "guild_id": "2", "channel_id": "3"})
        send.assert_awaited_once()

    def test_untrusted_surfaces_cannot_reach_executor(self):
        for kwargs in ({"user": 999}, {"guild": 999}, {"channel": 999},
                       {"guild": None}, {"webhook": 7}, {"bot": True}):
            with self.subTest(kwargs=kwargs), patch.object(discord_bot, "rpc") as rpc:
                send = self.invoke("!approve proposal digest", **kwargs)
                rpc.assert_not_called()
                send.assert_not_awaited()

    def test_generic_yes_is_not_approval(self):
        with patch.object(discord_bot, "rpc") as rpc:
            self.invoke("yes")
        rpc.assert_not_called()

    def test_read_does_not_open_writer_or_executor(self):
        core.record(self.db, self.check, True, "healthy")
        with patch.object(discord_bot, "rpc") as rpc, patch.object(discord_bot, "open_db", wraps=core.open_db) as opened:
            send = self.invoke("!read app")
        self.assertTrue(opened.call_args.kwargs["readonly"])
        self.assertIn("healthy", send.call_args.args[0])
        rpc.assert_not_called()


if __name__ == "__main__":
    unittest.main()
