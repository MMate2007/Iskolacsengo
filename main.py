import sqlite3
import json
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
from datetime import datetime, timedelta
from time import sleep
from flask import Flask, render_template, request, url_for, redirect, flash
import bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import threading
from math import ceil

allowedfiles = ["wav", "mp3", "ogg"]

app = Flask(__name__)
app.secret_key = "valami"
loginmanager = LoginManager()
loginmanager.init_app(app)
pygame.init()
with open("settings.json") as f:
		settings = json.load(f)
app.config["UPLOAD_FOLDER"] = settings["uploadFolder"]

events = []
lastloaded = 0
settings = []
bellEnabled = True

class SoundEvent():
	def __init__(self, time, sound, type, volume = 1):
		self.time = time
		self.sound = sound
		self.volume = volume
		self.type = type
		if volume is None:
			self.volume = 1
	def play(self):
		if self.type == 1:
			pygame.mixer.Channel(0).set_volume(self.volume)
			pygame.mixer.Channel(0).play(pygame.mixer.Sound(self.sound))

def readSettings():
	global settings
	settings = []
	with open("settings.json") as f:
		settings = json.load(f)

def loadTodaysProgramme():
	global events, lastloaded, settings
	events = []
	lastloaded = datetime.now().day
	loaddb = sqlite3.connect(settings["programmesDb"])
	loadcursor = loaddb.cursor()
	loadcursor.execute("DELETE FROM dates WHERE date < DATE('now', 'localtime')")
	loadcursor.execute("DELETE FROM customsounds WHERE date < DATE('now', 'localtime')")
	loaddb.commit()
	result = loadcursor.execute("SELECT pattern_id FROM dates WHERE date = DATE('now', 'localtime')").fetchone()
	if result is None:
		return
	patternid = result[0]
	results = loadcursor.execute("SELECT schedule_type, start, end, id, asset_id FROM schedule WHERE pattern_id = ? ORDER BY id", (patternid,)).fetchall()
	for result in results:
		if result[0] == 1:
			customfileresult = loadcursor.execute("SELECT asset_id FROM customsounds WHERE date = DATE('now', 'localtime') AND schedule_id = ? AND params = 1", (result[3], )).fetchone()
			if customfileresult is None:
				assetresult = loadcursor.execute("SELECT filepath, volume FROM assets WHERE id = ?", (settings["classStartAssetId"],)).fetchone()
			else:
				assetresult = loadcursor.execute("SELECT filepath, volume FROM assets WHERE id = ?", (customfileresult[0],)).fetchone()
			events.append(SoundEvent(datetime.strptime(result[1], "%H:%M"), assetresult[0], 1, assetresult[1]))
			customfileresult = loadcursor.execute("SELECT asset_id FROM customsounds WHERE date = DATE('now', 'localtime') AND schedule_id = ? AND params = 2", (result[3], )).fetchone()
			if customfileresult is None:
				assetresult = loadcursor.execute("SELECT filepath, volume FROM assets WHERE id = ?", (settings["classEndReminderAssetId"],)).fetchone()
			else:
				assetresult = loadcursor.execute("SELECT filepath, volume FROM assets WHERE id = ?", (customfileresult[0],)).fetchone()
			events.append(SoundEvent(datetime.strptime(result[2], "%H:%M")-timedelta(minutes=settings["classEndReminderMin"]), assetresult[0], 1, assetresult[1]))
			customfileresult = loadcursor.execute("SELECT asset_id FROM customsounds WHERE date = DATE('now', 'localtime') AND schedule_id = ? AND params = 3", (result[3], )).fetchone()
			if customfileresult is None:
				assetresult = loadcursor.execute("SELECT filepath, volume FROM assets WHERE id = ?", (settings["classEndAssetId"],)).fetchone()
			else:
				assetresult = loadcursor.execute("SELECT filepath, volume FROM assets WHERE id = ?", (customfileresult[0],)).fetchone()
			events.append(SoundEvent(datetime.strptime(result[2], "%H:%M"), assetresult[0], 1, assetresult[1]))
		if result[0] == 2:
			customfileresult = loadcursor.execute("SELECT asset_id FROM customsounds WHERE date = DATE('now', 'localtime') AND schedule_id = ?", (result[3], )).fetchone()
			if customfileresult is None:
				assetresult = loadcursor.execute("SELECT filepath, volume FROM assets WHERE id = ?", (result[4],)).fetchone()
			else:
				assetresult = loadcursor.execute("SELECT filepath, volume FROM assets WHERE id = ?", (customfileresult[0],)).fetchone()
			events.append(SoundEvent(datetime.strptime(result[1], "%H:%M"), assetresult[0], 1, assetresult[1]))
	loaddb.close()

class User():
	def __init__(self, id):
		db = sqlite3.connect(settings["usersDb"])
		cursor = db.cursor()
		result = cursor.execute("SELECT username FROM users WHERE id = ?", (id,)).fetchone()
		self.id = id
		if result is not None:
			self.name = result[0]
			self.authenticated = True
		else:
			self.authenticated = False
		db.close()
	
	def is_authenticated(self):
		return self.authenticated
	
	def is_active(self):
		return True
	
	def is_anonymous(self):
		return False
	
	def get_id(self):
		return str(self.id)

@loginmanager.user_loader
def user_loader(id):	
	db = sqlite3.connect(settings["usersDb"])
	cursor = db.cursor()
	result = cursor.execute("SELECT id FROM users WHERE id = ?", (id,)).fetchone()
	db.close()
	if result is None:
		return
	return User(id)

@app.route("/")
def home():
	if current_user.is_authenticated:
		return redirect(url_for("admin"))
	return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
	name = request.form.get("name")
	password = request.form.get("password")
	db = sqlite3.connect(settings["usersDb"])
	cursor = db.cursor()
	result = cursor.execute("SELECT id, password FROM users WHERE username = ?", (name,)).fetchone()
	db.close()
	if result is not None:
		if bcrypt.checkpw(password.encode("utf-8"), result[1]):
			login_user(User(result[0]))
			return redirect(url_for("admin"))
		else:
			flash("Helytelen jelszó!", "danger")
			return redirect(url_for("home"))
	else:
		flash("Helytelen felhasználónév!", "danger")
		return redirect(url_for("home"))

@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for("home"))

@app.route("/admin")
@login_required
def admin():
	return render_template("admin.html", bellEnabled=bellEnabled)

@app.route("/changepassword", methods=("GET", "POST"))
@login_required
def changepassword():
	if request.method == "POST":
		password = request.form.get("pass")
		password2 = request.form.get("pass2")
		if password != password2:
			flash("A két jelszó nem egyezik meg!", "warning")
			return render_template("changepassword.html")
		db = sqlite3.connect(settings["usersDb"])
		cursor = db.cursor()
		cursor.execute("UPDATE users SET password = ? WHERE id = ?", (bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()), current_user.id))
		db.commit()
		flash("Sikeres jelszómódosítás!", "success")
		db.close()
		return redirect(url_for("logout"))
	return render_template("changepassword.html")

@app.route("/reload")
@login_required
def reload():
	readSettings()
	loadTodaysProgramme()
	return redirect(url_for("admin"))

@app.route("/reboot")
@login_required
def reboot():
	os.system("sudo reboot now")
	return redirect(url_for("admin"))

@app.route("/shutdown")
@login_required
def shutdown():
	os.system("sudo shutdown now")
	return redirect(url_for("admin"))

@app.route("/changeBellStatus")
@login_required
def changeBellStatus():
	global bellEnabled
	if bellEnabled == True:
		bellEnabled = False
		pygame.mixer.Channel(0).stop()
	elif bellEnabled == False:
		bellEnabled = True
	return redirect(url_for("admin"))

@app.route("/setpatterns", methods=("GET", "POST"))
@login_required
def dates():
	if request.method == "POST":
		setptdb = sqlite3.connect(settings["programmesDb"])
		setptcursor = setptdb.cursor()
		start = datetime.strptime(request.form.get("start"), "%Y-%m-%d")
		end = datetime.strptime(request.form.get("end"), "%Y-%m-%d")
		current = start
		while (current <= end):
			setptcursor.execute("INSERT INTO dates (date, pattern_id) VALUES (?, ?)", (current.strftime("%Y-%m-%d"), request.form.get("pattern")))
			current += timedelta(days=1)
		setptdb.commit()
		flash("Csengetési rend sikeresen beállítva a megadott napokra!", "success")
		setptdb.close()
	getptdb = sqlite3.connect(settings["programmesDb"])
	getptcursor = getptdb.cursor()
	patterns = getptcursor.execute("SELECT id, friendlyname, description FROM patterns ORDER BY friendlyname").fetchall()
	getptdb.close()
	return render_template("setdate.html", patterns=patterns)

@app.route("/viewprogrammes")
@login_required
def viewdates():
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	results = cursor.execute("SELECT date, friendlyname FROM dates INNER JOIN patterns ON dates.pattern_id = patterns.id ORDER BY date").fetchall()
	db.close()
	return render_template("viewdates.html", dates=results)

@app.route("/deletedate/<date>")
@login_required
def deletedate(date):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	cursor.execute("DELETE FROM dates WHERE date = ?", (date,))
	db.commit()
	flash("Csengetési rend sikeresen törölve az adott napról!", "success")
	db.close()
	return redirect(url_for("viewdates"))

@app.route("/createpattern", methods=("GET", "POST"))
@login_required
def createpattern():
	if request.method == "POST":
		name = request.form.get("name")
		description = request.form.get("description")
		db = sqlite3.connect(settings["programmesDb"])
		cursor = db.cursor()
		cursor.execute("INSERT INTO patterns (friendlyname, description) VALUES (?,?)", (name,description))
		db.commit()
		flash("Csengetési rend sikeresen létrehozva!", "success")
		result = cursor.execute("SELECT id FROM patterns WHERE friendlyname = ?", (name,)).fetchone()
		db.close()
		return redirect(url_for("viewschedule", id=result[0]))
	return render_template("createpattern.html")

@app.route("/listpatterns")
@login_required
def listpatterns():
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	patterns = cursor.execute("SELECT * FROM patterns ORDER BY friendlyname").fetchall()
	db.close()
	return render_template("listpatterns.html", patterns=patterns)

@app.route("/deletepattern/<int:id>")
@login_required
def deletepattern(id):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	cursor.execute("DELETE FROM patterns WHERE id = ?", (id,))
	cursor.execute("DELETE FROM schedule WHERE pattern_id = ?", (id, ))
	cursor.execute("DELETE FROM dates WHERE pattern_id = ?", (id, ))
	db.commit()
	flash("Csengetési rend sikeresen törölve!", "success")
	db.close()
	return redirect(url_for("listpatterns"))

@app.route("/<int:id>/viewschedule")
@login_required
def viewschedule(id):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	results = cursor.execute("SELECT schedule.id, schedule_type, start, end, filepath FROM schedule LEFT OUTER JOIN assets ON schedule.asset_id = assets.id WHERE pattern_id = ? ORDER BY start", (id,)).fetchall()
	name = cursor.execute("SELECT friendlyname FROM patterns WHERE id = ?", (id,)).fetchone()
	db.close()
	return render_template("viewschedule.html", schedule=results, pattern_name=name[0], patternid=id)

@app.route("/<int:patternid>/deleteevent/<int:id>")
@login_required
def deleteschedule(patternid, id):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	cursor.execute("DELETE FROM schedule WHERE id = ?", (id,))
	db.commit()
	flash("Csengetési esemény sikeresen törölve!", "success")
	db.close()
	return redirect(url_for("viewschedule", id=patternid))

@app.route("/<int:patternid>/addevent/<int:eventtype>", methods=("GET", "POST"))
@login_required
def addevent(patternid, eventtype):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	name = cursor.execute("SELECT friendlyname FROM patterns WHERE id = ?", (patternid,)).fetchone()
	db.close()
	if eventtype == 1:
		if request.method == "POST":
			start = request.form.get("start")
			end = request.form.get("end")
			db = sqlite3.connect(settings["programmesDb"])
			cursor = db.cursor()
			cursor.execute("INSERT INTO schedule (pattern_id, schedule_type, start, end) VALUES (?,1,?,?)", (patternid,start,end))
			db.commit()
			flash("Tanóra sikeresen hozzáadva a csengetési rendhez!", "success")
			db.close()
		return render_template("addlesson.html", pattern_name=name[0])
	elif eventtype == 2:
		if request.method == "POST":
			time = request.form.get("time")
			assetid = request.form.get("asset")
			db = sqlite3.connect(settings["programmesDb"])
			cursor = db.cursor()
			cursor.execute("INSERT INTO schedule (pattern_id, schedule_type, start, asset_id) VALUES (?,2,?,?)", (patternid,time,assetid))
			db.commit()
			flash("Csengetés sikeresen hozzáadva a csengetési rendhez!", "success")
			db.close()
		db = sqlite3.connect(settings["programmesDb"])
		cursor = db.cursor()
		ringtones = cursor.execute("SELECT id, filepath FROM assets WHERE asset_type = 1").fetchall()
		db.close()
		return render_template("addring.html", pattern_name=name[0], ringtones=ringtones)

@app.route("/listassets")
@login_required
def listassets():
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	ringtones = cursor.execute("SELECT id, filepath, length, volume FROM assets WHERE asset_type = 1").fetchall()
	db.close()
	return render_template("listassets.html", ringtones=ringtones, previewplaying=pygame.mixer.Channel(3).get_busy())

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowedfiles

@app.route("/uploadringtone", methods=("GET", "POST"))
@login_required
def uploadringtone():
	if request.method == "POST":
		files = request.files.getlist("file")
		db = sqlite3.connect(settings["programmesDb"])
		cursor = db.cursor()
		for file in files:
			filename = secure_filename(file.filename)
			result = cursor.execute("SELECT id FROM assets WHERE filepath = ?", (os.path.join(app.config["UPLOAD_FOLDER"], filename), )).fetchall()
			if not result:
				if file and allowed_file(file.filename):
					file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
					db = sqlite3.connect(settings["programmesDb"])
					cursor = db.cursor()
					cursor.execute("INSERT INTO assets (asset_type, filepath, length) VALUES (1,?,?)", (os.path.join(app.config["UPLOAD_FOLDER"], filename), ceil(pygame.mixer.Sound(os.path.join(app.config["UPLOAD_FOLDER"], filename)).get_length())))
					db.commit()
					flash(os.path.join(app.config["UPLOAD_FOLDER"], filename)+" - Fájl sikeresen feltöltve!", "success")
				else:
					flash(os.path.join(app.config["UPLOAD_FOLDER"], filename)+" - Nem engedélyezett fájlnév!", "danger")
			else:
				flash(os.path.join(app.config["UPLOAD_FOLDER"], filename)+" - Ilyen nevű fájl már létezik!", "danger")
		db.close()
		return redirect(url_for("listassets"))
	return render_template("uploadringtone.html")

@app.route("/deleteasset/<int:id>")
@login_required
def deleteasset(id):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	result = cursor.execute("SELECT filepath FROM assets WHERE id = ?", (id,)).fetchone()
	cursor.execute("DELETE FROM assets WHERE id = ?", (id,))
	db.commit()
	db.close()
	os.remove(result[0])
	flash("Fájl sikeresen törölve!", "success")
	return redirect(url_for("listassets"))

@app.route("/playasset/<int:id>")
@login_required
def playasset(id):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	result = cursor.execute("SELECT filepath FROM assets WHERE id = ?", (id,)).fetchone()
	db.close()
	pygame.mixer.Channel(3).play(pygame.mixer.Sound(result[0]))
	return redirect(url_for("listassets"))

@app.route("/stoppreview")
@login_required
def stoppreview():
	pygame.mixer.Channel(3).stop()
	return redirect(url_for("listassets"))

@app.route("/setcustomfile/<date>", methods=("GET", "POST"))
@login_required
def setcustomfile(date):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	ringtones = cursor.execute("SELECT id, filepath, asset_type FROM assets").fetchall()
	patternid = cursor.execute("SELECT pattern_id FROM dates WHERE date = ?", (date, )).fetchone()
	schedule = cursor.execute("SELECT id, schedule_type, start, end, asset_id FROM schedule WHERE pattern_id = ? ORDER BY start", (patternid[0], )).fetchall()
	customfiles = cursor.execute("SELECT id, asset_id, schedule_id, params FROM customsounds WHERE date = ?", (date, )).fetchall()
	db.close()
	if request.method == "POST":
		db = sqlite3.connect(settings["programmesDb"])
		cursor = db.cursor()
		for s in schedule:
			if s[1] == 1:
				start = request.form.get(str(s[0])+"start")
				reminder = request.form.get(str(s[0])+"reminder")
				end = request.form.get(str(s[0])+"end")
				if start != "null":
					cursor.execute("INSERT INTO customsounds (date, asset_id, schedule_id, params) VALUES (?, ?, ?, '1')", (date, start, s[0]))
				else:
					cursor.execute("DELETE FROM customsounds WHERE date = ? AND schedule_id = ? AND params = '1'", (date, s[0]))
				if reminder != "null":
					cursor.execute("INSERT INTO customsounds (date, asset_id, schedule_id, params) VALUES (?, ?, ?, '2')", (date, reminder, s[0]))
				else:
					cursor.execute("DELETE FROM customsounds WHERE date = ? AND schedule_id = ? AND params = '2'", (date, s[0]))
				if end != "null":
					cursor.execute("INSERT INTO customsounds (date, asset_id, schedule_id, params) VALUES (?, ?, ?, '3')", (date, end, s[0]))
				else:
					cursor.execute("DELETE FROM customsounds WHERE date = ? AND schedule_id = ? AND params = '3'", (date, s[0]))
				db.commit()
			if s[1] == 2:
				sound = request.form.get(str(s[0]))
				if sound != "null":
					cursor.execute("INSERT INTO customsounds (date, asset_id, schedule_id) VALUES (?, ?, ?)", (date, sound, s[0]))
				else:
					cursor.execute("DELETE FROM customsounds WHERE date = ? AND schedule_id = ?", (date, s[0]))
				db.commit()
		flash("Sikeres mentés!", "success")
		ringtones = cursor.execute("SELECT id, filepath, asset_type FROM assets").fetchall()
		patternid = cursor.execute("SELECT pattern_id FROM dates WHERE date = ?", (date, )).fetchone()
		schedule = cursor.execute("SELECT id, schedule_type, start, end FROM schedule WHERE pattern_id = ? ORDER BY start", (patternid[0], )).fetchall()
		customfiles = cursor.execute("SELECT id, asset_id, schedule_id, params FROM customsounds WHERE date = ?", (date, )).fetchall()
		db.close()
	return render_template("setcustomfile.html", ringtones=ringtones, schedule=schedule, customfiles=customfiles)

@app.route("/register", methods=("GET", "POST"))
@login_required
def register():
	if request.method == "POST":
		name = request.form.get("name")
		password = request.form.get("password")
		password2 = request.form.get("password2")
		if password == password2:
			password = password.encode("utf-8")
			encryptedpassword = bcrypt.hashpw(password, bcrypt.gensalt())
			db = sqlite3.connect(settings["usersDb"])
			cursor = db.cursor()
			cursor.execute("INSERT INTO users (username, password) VALUES (?,?)", (name,encryptedpassword))
			db.commit()
			flash("Felhasználó sikeresen létrehozva!", "success")
			db.close()
			return redirect(url_for("listusers"))
		else:
			flash("A két jelszó nem egyezik!", "danger")
	return render_template("register.html")

@app.route("/listusers")
@login_required
def listusers():
	db = sqlite3.connect(settings["usersDb"])
	cursor = db.cursor()
	result = cursor.execute("SELECT id, username FROM users").fetchall()
	db.close()
	return render_template("listusers.html", users=result)

@app.route("/deleteuser/<int:id>")
@login_required
def deleteuser(id):
	db = sqlite3.connect(settings["usersDb"])
	cursor = db.cursor()
	cursor.execute("DELETE FROM users WHERE id = ?", (id,))
	db.commit()
	flash("Felhasználó sikeresen törölve!", "success")
	db.close()
	return redirect(url_for("listusers"))

@app.route("/settings", methods=("GET", "POST"))
@login_required
def settings():
	if request.method == "POST":
		for setting in list(settings.keys()):
			if request.form.get(setting).isdigit():
				settings[setting] = int(request.form.get(setting))
			else:
				settings[setting] = request.form.get(setting)
		with open("settings.json", "w") as f:
			json.dump(settings, f)
		flash("Sikeres módosítás!", "success")
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	ringtones = cursor.execute("SELECT id, filepath FROM assets WHERE asset_type = 1").fetchall()
	db.close()
	return render_template("settings.html", ringtones=ringtones, settings=settings)

readSettings()
loadTodaysProgramme()
thread = threading.Thread(target=lambda: app.run(debug=True, host="0.0.0.0", use_reloader=False))
thread.setDaemon(True)
thread.start()
while True:
	if lastloaded != datetime.now().day:
		loadTodaysProgramme()
	for event in events:
		if event.type == 1 and bellEnabled == False:
			events.remove(event)
			continue
		if event.time.hour == datetime.now().hour and event.time.minute == datetime.now().minute:
			event.play()
			events.remove(event)
	sleep(0.2)
