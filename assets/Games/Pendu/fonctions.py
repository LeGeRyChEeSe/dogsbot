from random import choice

import aiosqlite


async def create_db_pendu(connection: aiosqlite.Connection, cursor: aiosqlite.Cursor):
    await cursor.execute("""
                CREATE TABLE IF NOT EXISTS pendu(
                        id INTEGER PRIMARY KEY UNIQUE,
                        mot TEXT
                        )
                """)
    await connection.commit()


async def check_word_exists(cursor: aiosqlite.Cursor, mot):
    mots = await cursor.execute("""SELECT mot FROM pendu""")
    mots = mots.fetchall()
    for m in mots:
        if m[0] == mot:
            return True
    return False


async def insert_into_pendu(connection: aiosqlite.Connection, cursor: aiosqlite.Cursor, mot):
    if not await check_word_exists(cursor, mot):
        await cursor.execute("""
                    INSERT INTO pendu(mot) VALUES(?)
                    """, (mot,))
        await connection.commit()
        return True
    else:
        return False


async def delete_from_pendu(connection: aiosqlite.Connection, cursor: aiosqlite.Cursor, mot):
    if await check_word_exists(cursor, mot):
        await cursor.execute("""DELETE FROM pendu WHERE mot=?""", (mot,))
        await connection.commit()
        return True
    else:
        return False


async def word_init(connection: aiosqlite.Connection, cursor: aiosqlite.Cursor, taille_mot):
    await create_db_pendu(connection, cursor)
    mots = await cursor.execute("""SELECT mot FROM pendu""")
    mots = await mots.fetchall()
    mot = choice(mots)[0]
    while len(mot) > taille_mot:
        mot = choice(mots)[0]
    return mot


def user_choice(self):
    last_word_hidden = self.word_hidden
    self.word_hidden = ""

    for l in self.mot:
        if l in self.letters_list:
            self.word_hidden += l
        else:
            self.word_hidden += "_"

    if self.word_hidden == last_word_hidden:
        self.user_chances += 1

    return self.word_hidden, self.user_chances
