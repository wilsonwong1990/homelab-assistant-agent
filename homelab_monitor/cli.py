"""Service and manual entry points; no deployment or credential provisioning."""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import os
import sqlite3
import sys
import time

from .core import ConfigurationError, TransportError, deliver, load_config, open_db, poll, snapshot
from .executor import Denied, rpc, serve_executor
from .investigation import investigate_next, model_settings, queue_read


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="state/monitor.db")
    parser.add_argument("--config", default="monitoring.json")
    parser.add_argument("--socket", default="/run/homelab-executor/control.sock")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "poll", "monitor", "notify", "investigate", "worker", "status", "mcp"):
        commands.add_parser(name)
    heartbeat = commands.add_parser("heartbeat")
    heartbeat.add_argument("--max-age", type=int, default=180)
    read = commands.add_parser("request-read")
    read.add_argument("check")
    executor = commands.add_parser("executor")
    executor.add_argument("--policy", required=True)
    executor.add_argument("--action-db", required=True)
    executor.add_argument("--kill-switch", required=True)
    bot = commands.add_parser("discord")
    bot.add_argument("--identity", required=True)
    github = commands.add_parser("approve-github")
    github.add_argument("id")
    github.add_argument("digest")
    github.add_argument("comment_id", type=int)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    os.umask(0o027)
    try:
        if args.command == "executor":
            serve_executor(args.socket, args.action_db, args.policy, args.db, args.kill_switch)
            return 0
        if args.command == "discord":
            from .discord_bot import run_bot
            run_bot(args.identity, args.db, args.socket)
            return 0
        if args.command == "approve-github":
            result = rpc(args.socket, {
                "method": "approve", "id": args.id, "digest": args.digest,
                "lane": "github", "comment_id": args.comment_id,
            })
            print(json.dumps(result))
            return 0 if result["state"] == "succeeded" else 1
        if args.command == "mcp":
            from .mcp import serve
            with contextlib.closing(open_db(args.db, readonly=True)) as db:
                serve(db)
            return 0
        if args.command == "request-read":
            with contextlib.closing(open_db(args.db)) as db:
                queue_read(db, args.check)
            print("queued read-only local investigation")
            return 0
        if args.command in {"status", "heartbeat"}:
            with contextlib.closing(open_db(args.db, readonly=True)) as db:
                if args.command == "status":
                    print(json.dumps(snapshot(db), indent=2))
                else:
                    row = db.execute("SELECT updated FROM heartbeat WHERE id=1").fetchone()
                    if not row or time.time() - row["updated"] > args.max_age:
                        raise ConfigurationError("monitor heartbeat is stale or absent")
                    print("monitor heartbeat fresh")
            return 0
        config = load_config(args.config)
        if args.command == "validate":
            if "model" in config:
                model_settings(config)
            print("configuration valid; credentials and live access not tested")
            return 0
        db = open_db(args.db)
        if args.command == "poll":
            poll(config, db)
        elif args.command in {"worker", "investigate"}:
            model_settings(config)
            while True:
                worked = investigate_next(config, db)
                if args.command == "investigate":
                    break
                if not worked:
                    time.sleep(5)
        elif args.command == "notify":
            webhook = os.environ.get("DISCORD_WEBHOOK_URL")
            if not webhook:
                raise ConfigurationError("DISCORD_WEBHOOK_URL is required")
            while True:
                deliver(db, webhook)
                time.sleep(5)
        elif args.command == "monitor":
            while True:
                poll(config, db)
                time.sleep(config.get("interval", 60))
        db.close()
        return 0
    except KeyboardInterrupt:
        return 0
    except (ConfigurationError, TransportError, Denied, OSError, sqlite3.Error, ValueError) as error:
        logging.error("%s", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
