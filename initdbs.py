import sqlite3
import json
import bcrypt
from os import makedirs, path, getcwd
from json import dump
settings = {
	'programmesDb': "programmes.db",
	'usersDb': "users.db",
	'devicesDb': "devices.db",
	'classStartAssetId': None,
	'classStartRingpatternId': None,
	'classEndReminderAssetId': None,
	'classEndReminderRingpatternId': None,
	'classEndReminderMin': 5,
	'classEndAssetId': None,
	'classEndRingpatternId': None,
	'uploadFolder': None,
	'musicFadeOut': 5
}
try:
	with open("settings.json") as s:
		settingsfromfile = json.load(s)
		for key, value in settingsfromfile.items():
			settings[key] = value
except FileNotFoundError:
	pass
if settings["uploadFolder"] is None:
	settings["uploadFolder"] = getcwd()+"/assets"
	with open("settings.json", "w") as f:
		json.dump(settings, f)
if not path.isdir(settings["uploadFolder"]):
	makedirs(settings["uploadFolder"])

programmesdb = sqlite3.connect(settings["programmesDb"])
programmescursor = programmesdb.cursor()
with open("programmedbschema.sql") as f:
	programmescursor.executescript(f.read())
programmesdb.commit()
programmesdb.close()

devicesdb = sqlite3.connect(settings["devicesDb"])
devicescursor = devicesdb.cursor()
with open("devicedbschema.sql") as f:
	devicescursor.executescript(f.read())
devicesdb.commit()
devicesdb.close()

usersdb = sqlite3.connect(settings["usersDb"])
userscursor = usersdb.cursor()
with open("userdbschema.sql") as u:
	userscursor.executescript(u.read())
userscursor.execute("INSERT INTO users (username, password) VALUES ('admin',?)", (bcrypt.hashpw("admin".encode("utf-8"), bcrypt.gensalt()),))
permissions = [["reload", "Programok újratöltése"],
			    ["reboot", "Eszköz újraindítása"],
				["shutdown", "Eszköz leállítása"],
				["disablebell", "Csengetés letiltása/engedélyezése"],
				["setdates", "Napok hozzáadása és törlése"],
				["setcustomfiles", "Egyedi hangok beállítása"],
				["patterns", "Csengetési rendek megtekintése, létrehozása, módosítása és törlése"],
				["playbacks", "Csengetési renden kívüli bejátszások listázása, létrehozása és törlése"],
				["ringtones", "Csengőhangok megtekintése, feltöltése és törlése"],
				["music", "Zenék megtekintése, feltöltése és törlése"],
				["files", "Egyéb fájlok megtekintése, feltöltése és törlése"],
				["previewfiles", "Fájlok manuális lejátszása"],
				["listusers", "Felhasználók megtekintése"],
				["createusers", "Felhasználó létrehozása"],
				["deleteusers", "Felhasználó törlése"],
				["editpermissions", "Jogosultságok szerkesztése"],
				["editsettings", "Beállítások módosítása"],
	       		["changevolume", "Hangerő módosítása"],
				["announce", "Bemondás"],
				["setmusic", "Zenék beállítása napokra"],
				["disablemusic", "Zene letiltása"],
				["devices", "Eszközök hozzáadása, törlése"],
				["ringpatterns", "Fizikai csengetési minták létrehozása, módosítása és törlése"]
				]
for permission in permissions:
	userscursor.execute("INSERT INTO permissions (friendlyname, humanname) VALUES (?, ?)", (permission[0],permission[1]))
usersdb.commit()
results = userscursor.execute("SELECT id FROM permissions").fetchall()
adminid = userscursor.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
for result in results:
	userscursor.execute("INSERT INTO userpermissions (user_id, permission_id) VALUES (?, ?)", (adminid[0], result[0]))
usersdb.commit()
usersdb.close()