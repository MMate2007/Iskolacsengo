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
permissions = [["reload", "Programok újratöltése"],
			    ["reboot", "Eszköz újraindítása"],
				["shutdown", "Eszköz leállítása"],
				["disablebell", "Csengetés letiltása/engedélyezése"],
				["viewdates", "Napok listázása"],
				["setdates", "Csengetési rend hozzárendelése naphoz"],
				["deletedates", "Csengetési rend hozzárendelése megszüntetése adott naphoz"],
				["setcustomfiles", "Egyedi hangok beállítása"],
				["listpatterns", "Csengetési rendek megtekintése"],
				["createpatterns", "Csengetési rendek létrehozása"], 
				["deletepatterns", "Csengetési rendek törlése"],
				["listschedule", "Események megtekintése"],
				["addtoschedule", "Események hozzáadása csengetési rendekhez"],
				["deletefromschedule", "Események törlése csengetési rendekből"],
				["listplaybacks", "Csengetési renden kívüli bejátszások listázása"],
				["addplaybacks", "Csengetési renden kívüli bejátszás hozzáadása"],
				["deleteplaybacks", "Csengetési renden kívüli bejátszássok törlése"],
				["listringtones", "Csengőhangok megtekintése"],
				["listmusic", "Zenék megtekintése"],
				["listfiles", "Egyéb fájlok megtekintése"],
				["uploadringtones", "Csengőhangok feltöltése"],
				["deleteringtones", "Csengőhangok törlése"],
				["previewringtones", "Csengőhangok manuális lejátszása"],
				["uploadmusic", "Zene feltöltése"],
				["deletemusic", "Zene törlése"],
				["previewmusic", "Zene manuális lejátszása"],
				["uploadfiles", "Egyéb fájlok feltöltése"],
				["deletefiles", "Egyéb fájlok törlése"],
				["previewfiles", "Fájlok manuális lejátszása"],
				["listusers", "Felhasználók megtekintése"],
				["createusers", "Felhasználó létrehozása"],
				["deleteusers", "Felhasználó törlése"],
				["modifypasswords", "Más felhasználók jelszavának módosítása"],
				["editpermissions", "Jogosultságok szerkesztése"],
				["editsettings", "Beállítások módosítása"]
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
print("Ready.")