import sqlite3

from typing import List

db_path = "./assets/Data/pairs.db"


def db_connect(db=db_path):
    connection = sqlite3.connect(db)
    cursor = connection.cursor()
    return connection, cursor


def db_close(connection):
    connection.close()


def create(connection: sqlite3.Connection, cursor: sqlite3.Cursor, table, **kwargs):
    _names: list = kwargs.get("_names")
    _type = kwargs.get("_type")
    args = ""

    for i in range(len(_names)):
        if i != len(_names) - 1:
            args += f"{_names[i]} {_type[i]}, "
        else:
            args += f"{_names[i]} {_type[i]}"

    cursor.execute(f"""CREATE TABLE IF NOT EXISTS {table}(
                    id INTEGER PRIMARY KEY UNIQUE,
                    {args})""")
    connection.commit()
    print(f"La table {table} a été créée!")


def drop(connection: sqlite3.Connection, cursor: sqlite3.Cursor, table: str):
    try:
        cursor.execute(f"DROP TABLE {table}")
    except sqlite3.OperationalError:
        print(f"La table {table} n'existe pas!")
    else:
        connection.commit()
        print(f"La table {table} a bien été supprimée!")


def select(cursor: sqlite3.Cursor, **kwargs):
    _select: list = kwargs.get("_select") or "*"
    _from: str = kwargs.get("_from")
    _where: str = kwargs.get("_where")
    _fetchall: bool = kwargs.get("_fetchall") or False

    if _where:
        selection = cursor.execute(f"SELECT {','.join(_select)} FROM {_from} WHERE {_where}")
    else:
        selection = cursor.execute(f"SELECT {','.join(_select)} FROM {_from}")

    if not _fetchall:
        selection = selection.fetchone()
    else:
        selection = selection.fetchall()

    return selection


def insert(connection: sqlite3.Connection, cursor: sqlite3.Cursor, **kwargs):
    _into: str = kwargs.get("_into")
    _names: List[str] = kwargs.get("_names")
    _values: List[str] = kwargs.get("_values")

    for i in range(len(_values)):
        _values[i] = f'"{_values[i]}"'
    print(','.join(_names))
    print(','.join(_values))

    cursor.execute(f"INSERT INTO {_into}({','.join(_names)}) VALUES({','.join(_values)})")
    connection.commit()
    print(f"Les données ont bien été insérées dans la table {_into}!")


def delete(connection: sqlite3.Connection, cursor: sqlite3.Cursor, **kwargs):
    _from: str = kwargs.get("_from")
    _where: str = kwargs.get("_where")

    cursor.execute(f"DELETE FROM {_from} WHERE {_where}")
    print(f"La ligne a bien été supprimée!")
    connection.commit()
