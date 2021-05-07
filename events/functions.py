import json
from datetime import datetime
import random
import string

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

from typing import Dict
import discord

from discord.ext import commands

db_path = "./assets/Data/pairs.db"
log_file = "dogsbot.log"
dateFormatter = "%d/%m/%y %H:%M"


def team_dev(ctx: commands.Context):
    return ctx.author.id == 440141443877830656


def _test_file(file: str):
    try:
        open(file, "x").close()
    except FileExistsError:
        return True


def write_file(file: str, content: str, **kwargs):
    mode: str = kwargs.get("mode") or "a"
    is_log: bool = kwargs.get("is_log") or False
    is_json: bool = kwargs.get("is_json") or False
    ctx: commands.Context = kwargs.get("ctx") or None
    _test_file(file)
    if is_log:
        content = f"{datetime.utcnow()} | {content} | \n"
        with open(file, mode, encoding="utf-8") as the_file:
            the_file.write(content)

    elif is_json:
        with open(file, mode, encoding="utf-8") as the_file:
            json.dump(content, the_file, indent=4)
    else:
        with open(file, mode, encoding="utf-8") as the_file:
            the_file.write(content)


def read_file(file: str, **kwargs):
    is_json: bool = kwargs.get("is_json") or False
    _test_file(file)
    with open(file, "r", encoding="utf-8") as the_file:
        if is_json:
            return json.load(the_file)
        else:
            return the_file.read()


def set_file_logs(guild_id: int):
    return f"logs/{guild_id}.log"


def random_string(length: int):
    str = string.ascii_letters + string.digits
    return "".join(random.choice(str) for i in range(length))


async def get_log_channel(client: commands.Bot, ctx: commands.Context, message: str):
    try:
        guild_id = ctx.guild.id
    except AttributeError:
        guild_id = ctx.guild_id

    async with client.pool.acquire() as con:

        log_channel_id = await con.fetch('''
        SELECT channel_id
        FROM logs_channel
        WHERE guild_id = $1
        ''', guild_id)

    if log_channel_id:
        channel: discord.TextChannel = client.get_channel(
            log_channel_id[0].get('channel_id'))
        await channel.send(message)


async def set_score_participant(client: commands.Bot, ctx: commands.Context, id_participant: int, score: int = 0):
    async with client.pool.acquire() as con:

        current_score = await con.execute('''
        SELECT score
        FROM tournament_participants
        WHERE id_participant = $1
        ''', id_participant)

        await con.execute('''
        UPDATE tournament_participants
        SET score = $1
        WHERE id_participant = $2
        ''', current_score[0].get('score') + score, id_participant)


async def getLanplayStatus(url: str) -> Dict:
    """
            {
              room {
                hostPlayerName\n
                nodeCountMax\n
                nodeCount\n
                nodes {
                    playerName
                }\n
                contentId
              }\n
              serverInfo {
                online\n
                idle
              }
            }
    """

    transport = AIOHTTPTransport(
        url=url)

    # Using `async with` on the client will start a connection on the transport
    # and provide a `session` variable to execute queries on this connection
    async with Client(
        transport=transport, fetch_schema_from_transport=True,
    ) as session:

        # Execute single query
        query = gql(
            """
            query getUsers {
              room {
                hostPlayerName
                nodeCountMax
                nodeCount
                nodes {
                    playerName
                }
                contentId
              }
              serverInfo {
                online
                idle
              }
            }
        """
        )

        result = await session.execute(query)
        return result
