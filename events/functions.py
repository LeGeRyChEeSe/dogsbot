import json
import sqlite3
from datetime import datetime
import random
import string

import asyncio

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

import aiosqlite

from typing import Dict, List
import discord

from discord.ext import commands

db_path = "./assets/Data/pairs.db"
log_file = "dogsbot.log"
dateFormatter = "%d/%m/%y %H:%M"


async def db_connect(db=db_path):
    connection: aiosqlite.Connection = await aiosqlite.connect(db)
    cursor: aiosqlite.Cursor = await connection.cursor()
    return connection, cursor


async def db_close(connection):
    await connection.close()


async def create(connection: aiosqlite.Connection, cursor: aiosqlite.Cursor, table: str, **kwargs):

    # Permet de créer une table dans la base de données existente
    # Utiliser la syntaxe suivante:
    # create(connection, cursor, "nouvelle_table", _names=["guild_id", "insérer_texte"], _type=["INT", "TEXT"])

    _names: list = kwargs.get("_names")
    _type: list = kwargs.get("_type")
    args = ""

    for i in range(len(_names)):
        if i != len(_names) - 1:
            args += f"{_names[i]} {_type[i]}, "
        else:
            args += f"{_names[i]} {_type[i]}"

    await cursor.execute(f"""CREATE TABLE IF NOT EXISTS {table}(
                    id INTEGER PRIMARY KEY UNIQUE,
                    {args})""")
    await connection.commit()
    return f"La table {table} a été créée!"


async def drop(connection: aiosqlite.Connection, cursor: aiosqlite.Cursor, table: str):
    try:
        await cursor.execute(f"DROP TABLE {table}")
    except sqlite3.OperationalError:
        pass
    else:
        await connection.commit()


async def select(cursor: aiosqlite.Cursor, **kwargs):
    _select: list = kwargs.get("_select") or "*"
    _from: str = kwargs.get("_from")
    _where: str = kwargs.get("_where")
    _fetchall: bool = kwargs.get("_fetchall") or False

    if _where:
        selection = await cursor.execute(
            f"SELECT {','.join(_select)} FROM {_from} WHERE {_where}")
    else:
        selection = await cursor.execute(f"SELECT {','.join(_select)} FROM {_from}")

    if not _fetchall:
        selection = await selection.fetchone()
    else:
        selection = await selection.fetchall()

    return selection


async def insert(connection: aiosqlite.Connection, cursor: aiosqlite.Cursor, **kwargs):
    """ Example:

    connection, cursor = db_connect()
    cursor.execute(
        "INSERT INTO prefix(guild, prefix) VALUES(?, ?)", (guild.id, "!"))
    db_close(connection)

    """

    _into: str = kwargs.get("_into")
    _names: List[str] = kwargs.get("_names")
    _values: List[str] = kwargs.get("_values")

    for i in range(len(_values)):
        _values[i] = f'"{_values[i]}"'

    await cursor.execute(
        f"INSERT INTO {_into}({','.join(_names)}) VALUES({','.join(_values)})")
    await connection.commit()
    write_file(
        log_file, f"Des données ont été inséré dans la table {_into}!", is_log=True)


async def update(connection: aiosqlite.Connection, cursor: aiosqlite.Cursor, table: str, **kwargs):
    _set: tuple(str, str) = kwargs.get("set")
    _where: tuple(str, str) = kwargs.get("where")

    await cursor.execute(
        f"UPDATE {table} SET {_set[0]} = ? WHERE {_where[0]} = ?", (_set[1], _where[1]))
    await connection.commit()

    return "Ligne mise à jour!"


async def delete(connection: aiosqlite.Connection, cursor: aiosqlite.Cursor, **kwargs):
    _from: str = kwargs.get("_from")
    _where: str = kwargs.get("_where")

    await cursor.execute(f"DELETE FROM {_from} WHERE {_where}")
    await connection.commit()
    write_file(
        log_file, f"Des données ont été supprimées dans la table {_from}", is_log=True)


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
    connection, cursor = await db_connect()
    try:
        guild_id = ctx.guild.id
    except AttributeError:
        guild_id = ctx.guild_id

    log_channel_id = await cursor.execute("SELECT channel_id FROM logs_channel WHERE guild_id = ?", (guild_id,))

    if log_channel_id:
        log_channel_id = (await log_channel_id.fetchone())[0]
        channel: discord.TextChannel = client.get_channel(log_channel_id)
        await channel.send(message)


async def set_score_participant(client: commands.Bot, ctx: commands.Context, id_participant: int, score: int = 0):
    connection, cursor = await db_connect()

    current_score = await cursor.execute("SELECT score FROM tournament_participants WHERE id_participant = ?", (id_participant,))
    current_score = await current_score.fetchone()

    await cursor.execute("UPDATE tournament_participants SET score = ? WHERE id_participant = ?", (current_score + score, id_participant))
    await connection.commit()

    await db_close(connection)


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
