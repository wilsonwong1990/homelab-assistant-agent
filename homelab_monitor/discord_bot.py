"""Approval transport only; the executor owns authorization and credentials."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import sqlite3
import time

from .core import ConfigurationError, open_db, snapshot
from .executor import Denied, discord_actor, rpc

LOG = logging.getLogger(__name__)


def run_bot(settings_path, observer_path, socket_path):
    try:
        import discord
    except ImportError:
        raise ConfigurationError("Discord bot requires: pip install '.[discord]'") from None
    with open(settings_path) as source:
        settings = json.load(source)
    if not os.environ.get("DISCORD_BOT_TOKEN"):
        raise ConfigurationError("DISCORD_BOT_TOKEN is required")
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents, allowed_mentions=discord.AllowedMentions.none())
    cooldown = {}

    @client.event
    async def on_ready():
        LOG.info("Discord transport connected as user ID %s", client.user.id)

    @client.event
    async def on_message(message):
        if message.author.bot or message.webhook_id or message.guild is None:
            return
        context = {"user_id": str(message.author.id), "guild_id": str(message.guild.id),
                   "channel_id": str(message.channel.id)}
        try:
            discord_actor({"discord": settings}, context)
        except Denied:
            return
        if not message.content.startswith("!"):
            return
        previous = cooldown.get(context["user_id"])
        if previous is not None and time.monotonic() - previous < 3:
            return
        cooldown[context["user_id"]] = time.monotonic()
        parts = message.content.split()
        try:
            if parts == ["!status"]:
                with contextlib.closing(open_db(observer_path, readonly=True)) as db:
                    rows = snapshot(db)
                response = json.dumps(rows, indent=2)
            elif len(parts) == 2 and parts[0] == "!read":
                with contextlib.closing(open_db(observer_path, readonly=True)) as db:
                    check = db.execute("SELECT * FROM checks WHERE id=?", (parts[1],)).fetchone()
                    if check is None:
                        raise ConfigurationError("unknown check")
                    diagnosis = db.execute(
                        "SELECT result,state,updated FROM investigations JOIN events ON events.id=event_id WHERE check_id=? ORDER BY investigations.updated DESC LIMIT 1",
                        (parts[1],),
                    ).fetchone()
                response = json.dumps({"check": dict(check), "latest_analysis": dict(diagnosis) if diagnosis else None}, indent=2)
            elif len(parts) in (2, 3) and parts[0] == "!propose":
                issue = int(parts[2]) if len(parts) == 3 else None
                result = await asyncio.to_thread(rpc, socket_path, {
                    "method": "propose", "runbook": parts[1], "issue": issue})
                response = json.dumps(result, indent=2)
                if result["proposal"]["definition"]["lane"] == "discord":
                    response += f"\nTo approve this exact action: !approve {result['id']} {result['digest']}"
                else:
                    response += "\nGitHub approval required. Discord cannot authorize this proposal."
            elif len(parts) == 3 and parts[0] == "!approve":
                result = await asyncio.to_thread(rpc, socket_path, {
                    "method": "approve", "id": parts[1], "digest": parts[2],
                    "lane": "discord", "context": context})
                response = json.dumps(result)
            else:
                response = ("Commands: !status, !read CHECK, !propose RUNBOOK [ISSUE], "
                            "!approve ID SHA256. Configuration/higher-impact changes require GitHub.")
        except (Denied, ConfigurationError, ValueError, OSError, sqlite3.Error) as error:
            LOG.warning("Discord request rejected: %s", error)
            response = f"Request rejected or unavailable: {error}. No automatic retry."
        # Fixed data can still contain Markdown; mentions are disabled at the transport.
        if len(response) > 7600:
            response = "Response exceeds Discord display limit; use the local status command or read-only MCP bridge."
        for start in range(0, len(response), 1900):
            await message.channel.send(response[start:start + 1900])

    client.run(os.environ["DISCORD_BOT_TOKEN"], log_handler=None)
