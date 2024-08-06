import sqlite3
import json

def export():
    exporteddata = {}
    with open("settings.json") as s:
        exporteddata["settings"] = json.load(s)
    exporteddata["programmes"] = {}
    db = sqlite3.connect(exporteddata["settings"]["programmesDb"])
    cursor = db.cursor()

    tabledatas = cursor.execute("SELECT * FROM patterns").fetchall()
    table_columns = [desc[0] for desc in cursor.description]
    exporteddata["programmes"]["patterns"] = []
    for tabledata in tabledatas:
        entry = {}
        for id, column in enumerate(table_columns):
            entry[column] = tabledata[id]
        exporteddata["programmes"]["patterns"].append(entry)

    tabledatas = cursor.execute("SELECT * FROM schedule").fetchall()
    table_columns = [desc[0] for desc in cursor.description]
    exporteddata["programmes"]["schedule"] = []
    for tabledata in tabledatas:
        entry = {}
        for id, column in enumerate(table_columns):
            entry[column] = tabledata[id]
        exporteddata["programmes"]["schedule"].append(entry)
    
    tabledatas = cursor.execute("SELECT * FROM dates").fetchall()
    table_columns = [desc[0] for desc in cursor.description]
    exporteddata["programmes"]["dates"] = []
    for tabledata in tabledatas:
        entry = {}
        for id, column in enumerate(table_columns):
            entry[column] = tabledata[id]
        exporteddata["programmes"]["dates"].append(entry)
    
    tabledatas = cursor.execute("SELECT * FROM assets").fetchall()
    table_columns = [desc[0] for desc in cursor.description]
    exporteddata["programmes"]["assets"] = []
    for tabledata in tabledatas:
        entry = {}
        for id, column in enumerate(table_columns):
            entry[column] = tabledata[id]
        exporteddata["programmes"]["assets"].append(entry)

    tabledatas = cursor.execute("SELECT * FROM customsounds").fetchall()
    table_columns = [desc[0] for desc in cursor.description]
    exporteddata["programmes"]["customsounds"] = []
    for tabledata in tabledatas:
        entry = {}
        for id, column in enumerate(table_columns):
            entry[column] = tabledata[id]
        exporteddata["programmes"]["customsounds"].append(entry)
    
    tabledatas = cursor.execute("SELECT * FROM playbacks").fetchall()
    table_columns = [desc[0] for desc in cursor.description]
    exporteddata["programmes"]["playbacks"] = []
    for tabledata in tabledatas:
        entry = {}
        for id, column in enumerate(table_columns):
            entry[column] = tabledata[id]
        exporteddata["programmes"]["playbacks"].append(entry)

    db.close()
    exporteddata["users"] = {}
    db = sqlite3.connect(exporteddata["settings"]["usersDb"])
    cursor = db.cursor()

    tabledatas = cursor.execute("SELECT * FROM users").fetchall()
    table_columns = [desc[0] for desc in cursor.description]
    exporteddata["users"]["users"] = []
    for tabledata in tabledatas:
        entry = {}
        for id, column in enumerate(table_columns):
            if column == "password":
                entry[column] = str(tabledata[id])[2:-1]
            else:
                entry[column] = tabledata[id]
        permissions = cursor.execute("SELECT friendlyname FROM permissions INNER JOIN userpermissions ON permission_id = id WHERE user_id = ?", (entry["id"], )).fetchall()
        entry["permissions"] = [permission[0] for permission in permissions] 
        exporteddata["users"]["users"].append(entry)
    
    tabledatas = cursor.execute("SELECT * FROM permissions").fetchall()
    table_columns = [desc[0] for desc in cursor.description]
    exporteddata["users"]["permissions"] = []
    for tabledata in tabledatas:
        entry = {}
        for id, column in enumerate(table_columns):
            entry[column] = tabledata[id]
        exporteddata["users"]["permissions"].append(entry)
    
    tabledatas = cursor.execute("SELECT * FROM userpermissions").fetchall()
    table_columns = [desc[0] for desc in cursor.description]
    exporteddata["users"]["userpermissions"] = []
    for tabledata in tabledatas:
        entry = {}
        for id, column in enumerate(table_columns):
            entry[column] = tabledata[id]
        exporteddata["users"]["userpermissions"].append(entry)
    
    db.close()