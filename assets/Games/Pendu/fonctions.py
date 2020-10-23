from random import choice


def create_db_pendu(connection, cursor):
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS pendu(
                        id INTEGER PRIMARY KEY UNIQUE,
                        mot TEXT
                        )
                """)
    connection.commit()


def check_word_exists(cursor, mot):
    mots = cursor.execute("""SELECT mot FROM pendu""").fetchall()
    for m in mots:
        if m[0] == mot:
            return True
    return False


def insert_into_pendu(connection, cursor, mot):
    if not check_word_exists(cursor, mot):
        cursor.execute("""
                    INSERT INTO pendu(mot) VALUES(?)
                    """, (mot,))
        connection.commit()
        return True
    else:
        return False


def delete_from_pendu(connection, cursor, mot):
    if check_word_exists(cursor, mot):
        cursor.execute("""DELETE FROM pendu WHERE mot=?""", (mot,))
        connection.commit()
        return True
    else:
        return False


def word_init(connection, cursor, taille_mot):
    create_db_pendu(connection, cursor)
    mots = cursor.execute("""SELECT mot FROM pendu""").fetchall()
    mot = choice(mots)[0]
    while len(mot) > taille_mot:
        mot = choice(mots)[0]
    return mot


async def user_choice(self):
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
