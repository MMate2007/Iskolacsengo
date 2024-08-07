import sqlite3
import json
from datetime import datetime
from os import path
from werkzeug.utils import secure_filename

def export(user = None, filename = "iskolacsengo-export"+datetime.now().strftime("%Y%m%d-%H%M%S")+".json", savetofile = True, filepath = path.dirname(path.realpath(__file__))):
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
    
    tabledatas = cursor.execute("SELECT friendlyname FROM permissions").fetchall()
    exporteddata["users"]["permissions"] = [tabledata[0] for tabledata in tabledatas]
    db.close()
    if user is not None:
        exporteddata["exportuser"] = user
    if savetofile == True:
        filename = secure_filename(filename)
        fpath = path.join(filepath, filename)
        with open(fpath, "x") as f:
            json.dump(exporteddata, f)
        return fpath
    elif savetofile == False:
        return exporteddata

def importfromfile(file):
    with open(file) as f:
        importdata = json.load(f)
        settings = None
        with open("settings.json") as s:
            settings = json.load(s)
        for key, value in importdata["settings"].items():
            settings[key] = value
        with open("settings.json", "w") as s:
            json.dump(settings, s)
        
        db = sqlite3.connect(importdata["settings"]["programmesDb"])
        cursor = db.cursor()
        tables = [t for t in importdata["programmes"]]
        for table in tables:
            if table not in [t[0] for t in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
                continue
            if importdata["programmes"][table] == []:
                continue
            cursor.execute("SELECT * FROM "+table)
            columns = [desc[0] for desc in cursor.description]
            for column in columns:
                if column not in importdata["programmes"][table][0]:
                    columns.remove(column)
            for entry in importdata["programmes"][table]:
                sql = "INSERT INTO "+table+" ("
                for column in columns:
                    sql += column+", "
                sql = sql[:-2]
                sql += ") VALUES ("
                for column in columns:
                    sql += "?,"
                sql = sql[:-1]
                sql += ")"
                parameters = []
                for column in columns:
                    parameters.append(entry[column])
                cursor.execute(sql, tuple(parameters))
        db.commit()
        db.close()