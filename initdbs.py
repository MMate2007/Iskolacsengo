import sqlite3
import json
import bcrypt

with open("settings.json") as s:
	settings = json.load(s)

programmesdb = sqlite3.connect(settings["programmesDb"])
programmescursor = programmesdb.cursor()
with open("programmedbschema.sql") as f:
	programmescursor.executescript(f.read())
programmesdb.commit()
programmesdb.close()

usersdb = sqlite3.connect(settings["usersDb"])
userscursor = usersdb.cursor()
with open("userdbschema.sql") as u:
	userscursor.executescript(u.read())
userscursor.execute("INSERT INTO users (username, password) VALUES ('admin',?)", (bcrypt.hashpw("admin".encode("utf-8"), bcrypt.gensalt()),))
usersdb.commit()
usersdb.close()
print("Ready.")