import sqlite3
import json
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
from datetime import datetime, timedelta
from time import sleep
from flask import Flask, render_template, request, url_for, redirect, flash, Markup
import bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import threading
from math import ceil
from functools import wraps
import alsaaudio
from gpiozero import CPUTemperature, DiskUsage, LoadAverage
from pydub import AudioSegment, effects

allowedfiles = ["wav", "mp3", "ogg", "m4a"]

app = Flask(__name__)
app.secret_key = "valami"
loginmanager = LoginManager()
loginmanager.init_app(app)
pygame.mixer.init(buffer=2048, channels=4)
alsamixer = alsaaudio.Mixer()
with open("settings.json") as f:
		settings = json.load(f)
app.config["UPLOAD_FOLDER"] = settings["uploadFolder"]

events = []
lastloaded = 0
settings = []
bellEnabled = True
customplaybackEnabled = True
musicEnabled = True
music = []
musicpos = 0

class SoundEvent():
	def __init__(self, time, sound, type):
		self.time = time
		self.sound = sound
		self.type = type
	def play(self):
		if self.type == 1:
			pygame.mixer.Channel(0).play(pygame.mixer.Sound(self.sound))
		if self.type == 2:
			pygame.mixer.Channel(1).play(pygame.mixer.Sound(self.sound))

class MusicEvent():
	def __init__(self, time, music):
		self.time = time
		self.music = music
		self.sound = "Zene"

	def play(self):
		global music, musicpos
		music = self.music
		pygame.mixer.music.load(music.pop())
		pygame.mixer.music.play()
		musicpos = pygame.mixer.music.get_pos()
		if music != []:
			pygame.mixer.music.queue(music.pop())

class MusicFadeEvent():
	def __init__(self, time, fade):
		self.time = time
		self.fade = fade
		self.sound = "Zene elhalkítása"
	
	def play(self):
		pygame.mixer.music.fadeout(self.fade*1000)
		pygame.mixer.music.unload()

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
	loadcursor.execute("DELETE FROM playbacks WHERE date < DATE('now', 'localtime')")
	loaddb.commit()
	results = loadcursor.execute("SELECT time, filepath FROM playbacks INNER JOIN assets ON playbacks.asset_id = assets.id WHERE date = DATE('now', 'localtime') ORDER BY time").fetchall()
	for result in results:
		events.append(SoundEvent(datetime.strptime(result[0], "%H:%M"), result[1], 2))
	result = loadcursor.execute("SELECT pattern_id FROM dates WHERE date = DATE('now', 'localtime')").fetchone()
	if result is None:
		loaddb.close()
		return
	patternid = result[0]
	results = loadcursor.execute("SELECT schedule_type, start, end, id, asset_id FROM schedule WHERE pattern_id = ? ORDER BY start, schedule_type", (patternid,)).fetchall()
	for result in results:
		if result[0] == 1:
			customfileresult = loadcursor.execute("SELECT asset_id FROM customsounds WHERE date = DATE('now', 'localtime') AND schedule_id = ? AND params = 1", (result[3], )).fetchone()
			if customfileresult is None:
				assetresult = loadcursor.execute("SELECT filepath FROM assets WHERE id = ?", (settings["classStartAssetId"],)).fetchone()
			else:
				assetresult = loadcursor.execute("SELECT filepath FROM assets WHERE id = ?", (customfileresult[0],)).fetchone()
			events.append(SoundEvent(datetime.strptime(result[1], "%H:%M"), assetresult[0], 1))
			if settings["classEndReminderMin"] != 0:
				customfileresult = loadcursor.execute("SELECT asset_id FROM customsounds WHERE date = DATE('now', 'localtime') AND schedule_id = ? AND params = 2", (result[3], )).fetchone()
				if customfileresult is None:
					assetresult = loadcursor.execute("SELECT filepath FROM assets WHERE id = ?", (settings["classEndReminderAssetId"],)).fetchone()
				else:
					assetresult = loadcursor.execute("SELECT filepath FROM assets WHERE id = ?", (customfileresult[0],)).fetchone()
				events.append(SoundEvent(datetime.strptime(result[2], "%H:%M")-timedelta(minutes=settings["classEndReminderMin"]), assetresult[0], 1))
			customfileresult = loadcursor.execute("SELECT asset_id FROM customsounds WHERE date = DATE('now', 'localtime') AND schedule_id = ? AND params = 3", (result[3], )).fetchone()
			if customfileresult is None:
				assetresult = loadcursor.execute("SELECT filepath FROM assets WHERE id = ?", (settings["classEndAssetId"],)).fetchone()
			else:
				assetresult = loadcursor.execute("SELECT filepath FROM assets WHERE id = ?", (customfileresult[0],)).fetchone()
			events.append(SoundEvent(datetime.strptime(result[2], "%H:%M"), assetresult[0], 1))
		if result[0] == 2:
			customfileresult = loadcursor.execute("SELECT asset_id FROM customsounds WHERE date = DATE('now', 'localtime') AND schedule_id = ?", (result[3], )).fetchone()
			if customfileresult is None:
				assetresult = loadcursor.execute("SELECT filepath FROM assets WHERE id = ?", (result[4],)).fetchone()
			else:
				assetresult = loadcursor.execute("SELECT filepath FROM assets WHERE id = ?", (customfileresult[0],)).fetchone()
			events.append(SoundEvent(datetime.strptime(result[1], "%H:%M"), assetresult[0], 1))
		if result[0] == 3:
			getmusic = loadcursor.execute("SELECT filepath FROM assets INNER JOIN customsounds ON assets.id = customsounds.asset_id WHERE customsounds.date = DATE('now', 'localtime') AND customsounds.schedule_id = ? ORDER BY customsounds.params DESC", (result[3], )).fetchall()
			if getmusic != []:
				music = []
				for entry in getmusic:
					music.append(entry[0])
				events.append(MusicEvent(datetime.strptime(result[1], "%H:%M"), music))
				events.append(MusicFadeEvent(datetime.strptime(result[2], "%H:%M")-timedelta(seconds=settings["musicFadeOut"]), settings["musicFadeOut"]))
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

	def haspermission(self, permission):
		db = sqlite3.connect(settings["usersDb"])
		cursor = db.cursor()
		result = cursor.execute("SELECT COUNT(*) FROM userpermissions INNER JOIN permissions ON permission_id = id WHERE friendlyname = ? AND user_id = ?", (permission, self.id)).fetchone()
		db.close()
		return result[0]

def permission_required(permission):
	def decorator(f):
		@wraps(f)
		def inner(*args, **kwargs):
			global loginmanager
			if current_user.haspermission(permission):
				pass
			else:
				return loginmanager.unauthorized()
			return f(*args, **kwargs)
		return inner
	return decorator


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

@app.route("/admin", methods=("GET", "POST"))
@login_required
def admin():
	if request.method == "POST" and current_user.haspermission("changevolume"):
		volume = int(request.form.get("volume"))
		alsamixer.setvolume(volume)
	cpu = CPUTemperature()
	load = LoadAverage()
	disk = DiskUsage()
	return render_template("admin.html", bellEnabled=bellEnabled, volume=alsamixer.getvolume(), cputemp=cpu.temperature, cpuload=load.load_average, diskusage=disk.usage, customplaybackEnabled=customplaybackEnabled, events=events, musicEnabled=musicEnabled)

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
@permission_required("reload")
def reload():
	readSettings()
	loadTodaysProgramme()
	return redirect(url_for("admin"))

@app.route("/reboot")
@login_required
@permission_required("reboot")
def reboot():
	os.system("sudo reboot now")
	return redirect(url_for("admin"))

@app.route("/shutdown")
@login_required
@permission_required("shutdown")
def shutdown():
	os.system("sudo shutdown now")
	return redirect(url_for("admin"))

@app.route("/changeBellStatus")
@login_required
@permission_required("disablebell")
def changeBellStatus():
	global bellEnabled
	if bellEnabled == True:
		bellEnabled = False
		pygame.mixer.Channel(0).stop()
	elif bellEnabled == False:
		bellEnabled = True
	return redirect(url_for("admin"))

@app.route("/changeMusicStatus")
@login_required
@permission_required("disablemusic")
def changeMusicStatus():
	global musicEnabled
	if musicEnabled == True:
		musicEnabled = False
		pygame.mixer.music.stop()
		pygame.mixer.music.unload()
	elif musicEnabled == False:
		musicEnabled = True
	return redirect(url_for("admin"))

@app.route("/changeCustomplaybackStatus")
@login_required
@permission_required("disablebell")
def changeCustomplaybackStatus():
	global customplaybackEnabled
	if customplaybackEnabled == True:
		customplaybackEnabled = False
		pygame.mixer.Channel(1).stop()
	elif customplaybackEnabled == False:
		customplaybackEnabled = True
	return redirect(url_for("admin"))

@app.route("/announce", methods=("GET", "POST"))
@login_required
@permission_required("announce")
def announce():
	if request.method == "POST":
		file = request.files['file']
		filename = secure_filename(file.filename)
		if file and allowed_file(file.filename):
			file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
			audio = AudioSegment.from_file(os.path.join(app.config["UPLOAD_FOLDER"], filename))
			normalised = effects.normalize(audio)
			normalised.export(os.path.join(app.config["UPLOAD_FOLDER"], "bemondas.wav"), format="wav")
			pygame.mixer.Channel(3).play(pygame.mixer.Sound(os.path.join(app.config["UPLOAD_FOLDER"], "bemondas.wav")))
			os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filename))
			os.remove(os.path.join(app.config["UPLOAD_FOLDER"], "bemondas.wav"))
			flash("A bemondás elkezdődött!", "success")
			return redirect(url_for("announce"))
		else:
			flash("Valami nem sikerült!", "danger")
			return redirect(url_for("announce"))
	return render_template("announce.html")

@app.route("/playprogramme/<int:id>/<time>")
@login_required
@permission_required("previewfiles")
def playprogramme(id, time):
	if events[id].time.strftime("%Y-%m-%d %H:%M:%S") == time:
		events[id].play()
		events.pop(id)
	return redirect(url_for("admin"))

@app.route("/deleteprogramme/<int:id>/<time>")
@login_required
@permission_required("patterns")
@permission_required("playbacks")
def deleteprogramme(id, time):
	if events[id].time.strftime("%Y-%m-%d %H:%M:%S") == time:
		events.pop(id)
	return redirect(url_for("admin"))

@app.route("/setpatterns", methods=("GET", "POST"))
@login_required
@permission_required("setdates")
def dates():
	if request.method == "POST":
		setptdb = sqlite3.connect(settings["programmesDb"])
		setptcursor = setptdb.cursor()
		start = datetime.strptime(request.form.get("start"), "%Y-%m-%d")
		end = datetime.strptime(request.form.get("end"), "%Y-%m-%d")
		days = list(map(int, request.form.getlist("days[]")))
		current = start
		while (current <= end):
			if current.weekday() in days:
				setptcursor.execute("INSERT OR REPLACE INTO dates (date, pattern_id) VALUES (?, ?)", (current.strftime("%Y-%m-%d"), request.form.get("pattern")))
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
	results = cursor.execute("SELECT date, friendlyname, EXISTS(SELECT 1 FROM customsounds INNER JOIN schedule ON customsounds.schedule_id = schedule.id WHERE customsounds.date = dates.date AND schedule.schedule_type != 3), EXISTS(SELECT 1 FROM customsounds INNER JOIN schedule ON customsounds.schedule_id = schedule.id WHERE customsounds.date = dates.date AND schedule.schedule_type = 3), EXISTS(SELECT 1 FROM playbacks WHERE playbacks.date = dates.date), EXISTS(SELECT 1 FROM schedule WHERE schedule_type = 3 AND schedule.pattern_id = patterns.id) FROM dates INNER JOIN patterns ON dates.pattern_id = patterns.id ORDER BY date").fetchall()
	db.close()
	return render_template("viewdates.html", dates=results)

@app.route("/deletedate/<date>")
@login_required
@permission_required("setdates")
def deletedate(date):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	cursor.execute("DELETE FROM dates WHERE date = ?", (date,))
	cursor.execute("DELETE FROM customsounds WHERE date = ?", (date,))
	db.commit()
	flash("Csengetési rend sikeresen törölve az adott napról!", "success")
	db.close()
	return redirect(url_for("viewdates"))

@app.route("/createpattern", methods=("GET", "POST"))
@login_required
@permission_required("patterns")
def createpattern():
	if request.method == "POST":
		name = request.form.get("name")
		description = request.form.get("description")
		db = sqlite3.connect(settings["programmesDb"])
		cursor = db.cursor()
		try:
			cursor.execute("INSERT INTO patterns (friendlyname, description) VALUES (?,?)", (name,description))
			db.commit()
		except sqlite3.IntegrityError:
			flash("Már létezik egy "+name+" nevű csengetési rend!", "danger")
			db.close()
			return redirect(url_for("createpattern"))
		flash("Csengetési rend sikeresen létrehozva!", "success")
		result = cursor.execute("SELECT id FROM patterns WHERE friendlyname = ?", (name,)).fetchone()
		db.close()
		return redirect(url_for("viewschedule", id=result[0]))
	return render_template("createpattern.html")

@app.route("/listpatterns")
@login_required
@permission_required("patterns")
def listpatterns():
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	patterns = cursor.execute("SELECT * FROM patterns ORDER BY friendlyname").fetchall()
	db.close()
	return render_template("listpatterns.html", patterns=patterns)

@app.route("/deletepattern/<int:id>")
@login_required
@permission_required("patterns")
def deletepattern(id):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	cursor.execute("DELETE FROM customsounds WHERE date in (SELECT date FROM dates WHERE pattern_id = ?)", (id, ))
	cursor.execute("DELETE FROM patterns WHERE id = ?", (id,))
	cursor.execute("DELETE FROM schedule WHERE pattern_id = ?", (id, ))
	cursor.execute("DELETE FROM dates WHERE pattern_id = ?", (id, ))
	db.commit()
	flash("Csengetési rend sikeresen törölve!", "success")
	db.close()
	return redirect(url_for("listpatterns"))

@app.route("/<int:id>/viewschedule")
@login_required
@permission_required("patterns")
def viewschedule(id):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	results = cursor.execute("SELECT schedule.id, schedule_type, start, end, filepath FROM schedule LEFT OUTER JOIN assets ON schedule.asset_id = assets.id WHERE pattern_id = ? ORDER BY start, schedule_type", (id,)).fetchall()
	name = cursor.execute("SELECT friendlyname FROM patterns WHERE id = ?", (id,)).fetchone()
	db.close()
	return render_template("viewschedule.html", schedule=results, pattern_name=name[0], patternid=id)

@app.route("/<int:patternid>/deleteevent/<int:id>")
@login_required
@permission_required("patterns")
def deleteschedule(patternid, id):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	cursor.execute("DELETE FROM schedule WHERE id = ?", (id,))
	cursor.execute("DELETE FROM customsounds WHERE schedule_id = ? AND date IN (SELECT date FROM dates WHERE pattern_id = ?)", (id, patternid, ))
	db.commit()
	flash("Csengetési esemény sikeresen törölve!", "success")
	db.close()
	return redirect(url_for("viewschedule", id=patternid))

@app.route("/<int:patternid>/addevent/<int:eventtype>", methods=("GET", "POST"))
@login_required
@permission_required("patterns")
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
	elif eventtype == 3:
		if request.method == "POST":
			start = request.form.get("start")
			end = request.form.get("end")
			db = sqlite3.connect(settings["programmesDb"])
			cursor = db.cursor()
			cursor.execute("INSERT INTO schedule (pattern_id, schedule_type, start, end) VALUES (?,3,?,?)", (patternid,start,end))
			db.commit()
			flash("Zenei blokk sikeresen hozzáadva a csengetési rendhez!", "success")
			db.close()
		return render_template("addlesson.html", pattern_name=name[0])


@app.route("/listassets")
@login_required
def listassets():
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	if current_user.haspermission("ringtones"):
		ringtones = cursor.execute("SELECT id, filepath, length FROM assets WHERE asset_type = 1").fetchall()
	else:
		ringtones = []
	if current_user.haspermission("music"):
		musiclist = cursor.execute("SELECT id, filepath, length FROM assets WHERE asset_type = 2").fetchall()
	else:
		musiclist = []
	if current_user.haspermission("files"):
		files = cursor.execute("SELECT id, filepath, length FROM assets WHERE asset_type = 3").fetchall()
	else:
		files = []
	db.close()
	return render_template("listassets.html", ringtones=ringtones, previewplaying=pygame.mixer.Channel(3).get_busy(), musiclist=musiclist, files=files)

@app.route("/audio/<int:id>/normalise")
@login_required
def normalise(id):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	result = cursor.execute("SELECT filepath, asset_type FROM assets WHERE id = ?", (id,)).fetchone()
	ftype = result[1]
	if not current_user.haspermission('ringtones') and ftype == 1:
		flash("Nincs jogosultsága csengőhang normalizálásához!", "danger")
		return redirect(url_for("listassets"))
	if not current_user.haspermission("music") and ftype == 2:
		flash("Nincs jogosultsága zene normalizálásához!", "danger")
		return redirect(url_for("listassets"))
	if not current_user.haspermission("files") and ftype == 3:
		flash("Nincs jogosultsága egyéb fájlok normalizálásához!", "danger")
		return redirect(url_for("listassets"))
	sound = AudioSegment.from_file(result[0])
	normalised = effects.normalize(sound)
	normalised.export(result[0])
	flash("Sikeres normalizálás!", "success")
	return redirect(url_for("listassets"))

@app.route("/audio/<int:id>/converttomono")
@login_required
def converttomono(id):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	result = cursor.execute("SELECT filepath, asset_type FROM assets WHERE id = ?", (id,)).fetchone()
	ftype = result[1]
	if not current_user.haspermission('ringtones') and ftype == 1:
		flash("Nincs jogosultsága csengőhang monósításához!", "danger")
		return redirect(url_for("listassets"))
	if not current_user.haspermission("music") and ftype == 2:
		flash("Nincs jogosultsága zene monósításához!", "danger")
		return redirect(url_for("listassets"))
	if not current_user.haspermission("files") and ftype == 3:
		flash("Nincs jogosultsága egyéb fájlok monósításához!", "danger")
		return redirect(url_for("listassets"))
	sound = AudioSegment.from_file(result[0])
	sound = sound.set_channels(1)
	sound.export(result[0])
	flash("Sikeres monósítás!", "success")
	return redirect(url_for("listassets"))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowedfiles

@app.route("/uploadfile", methods=("GET", "POST"))
@login_required
def uploadfile():
	if request.method == "POST":
		files = request.files.getlist("file")
		ftype = int(request.form.get("type"))
		if not current_user.haspermission('ringtones') and ftype == 1:
			flash("Nincs jogosultsága csengőhang feltöltéséhez!", "danger")
			return redirect(url_for("listassets"))
		if not current_user.haspermission("music") and ftype == 2:
			flash("Nincs jogosultsága zene feltöltéséhez!", "danger")
			return redirect(url_for("listassets"))
		if not current_user.haspermission("files") and ftype == 3:
			flash("Nincs jogosultsága egyéb fájlok feltöltéséhez!", "danger")
			return redirect(url_for("listassets"))
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
					cursor.execute("INSERT INTO assets (asset_type, filepath, length) VALUES (?,?,?)", (ftype, os.path.join(app.config["UPLOAD_FOLDER"], filename), ceil(pygame.mixer.Sound(os.path.join(app.config["UPLOAD_FOLDER"], filename)).get_length())))
					db.commit()
					flash(os.path.join(app.config["UPLOAD_FOLDER"], filename)+" - Fájl sikeresen feltöltve!", "success")
				else:
					flash(os.path.join(app.config["UPLOAD_FOLDER"], filename)+" - Nem engedélyezett fájlnév!", "danger")
			else:
				flash(os.path.join(app.config["UPLOAD_FOLDER"], filename)+" - Ilyen nevű fájl már létezik!", "danger")
		db.close()
		return redirect(url_for("listassets"))
	return render_template("uploadfile.html")

@app.route("/deleteasset/<int:id>")
@login_required
def deleteasset(id):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	result = cursor.execute("SELECT filepath, asset_type FROM assets WHERE id = ?", (id,)).fetchone()
	if result[1] == 1 and not current_user.haspermission("ringtones"):
		flash("Nincs jogosultsága csengőhang törléséhez!", "danger")
		return redirect(url_for("listassets"))
	if result[1] == 2 and not current_user.haspermission("music"):
		flash("Nincs jogosultsága zene törléséhez!", "danger")
		return redirect(url_for("listassets"))
	if result[1] == 3 and not current_user.haspermission("files"):
		flash("Nincs jogosultsága egyéb fájl törléséhez!", "danger")
		return redirect(url_for("listassets"))
	cursor.execute("DELETE FROM assets WHERE id = ?", (id,))
	db.commit()
	db.close()
	os.remove(result[0])
	flash("Fájl sikeresen törölve!", "success")
	return redirect(url_for("listassets"))

@app.route("/playasset/<int:id>")
@login_required
@permission_required("previewfiles")
def playasset(id):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	result = cursor.execute("SELECT filepath, asset_type FROM assets WHERE id = ?", (id,)).fetchone()
	if not current_user.haspermission("ringtones") and result[1] == 1:
		flash("Nincs jogosultsága csengőhang manuális lejátszásához!", "danger")
		redirect(url_for("listassets"))
	if not current_user.haspermission("music") and result[1] == 2:
		flash("Nincs jogosultsága zene manuális lejátszásához!", "danger")
		redirect(url_for("listassets"))
	if not current_user.haspermission("files") and result[1] == 3:
		flash("Nincs jogosultsága egyéb fájl manuális lejátszásához!", "danger")
		redirect(url_for("listassets"))
	db.close()
	pygame.mixer.Channel(3).play(pygame.mixer.Sound(result[0]))
	return redirect(url_for("listassets"))

@app.route("/stoppreview")
@login_required
@permission_required("previewfiles")
def stoppreview():
	pygame.mixer.Channel(3).stop()
	return redirect(url_for("listassets"))

@app.route("/setcustomfile/<date>", methods=("GET", "POST"))
@login_required
@permission_required("setcustomfiles")
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

@app.route("/viewmusic/<string:date>")
@login_required
@permission_required("setmusic")
def viewmusic(date):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	blocks = cursor.execute("SELECT id, start, end FROM schedule WHERE schedule_type = 3 AND pattern_id = (SELECT pattern_id FROM dates WHERE date = ?)", (date, )).fetchall()
	music = []
	times = []
	for block in blocks:
		music.append(cursor.execute("SELECT customsounds.id, filepath, length FROM customsounds INNER JOIN assets ON customsounds.asset_id = assets.id WHERE schedule_id = ? AND date = ? ORDER BY params", (block[0], date)).fetchall())
		timesum = cursor.execute("SELECT SUM(length) FROM assets INNER JOIN customsounds ON customsounds.asset_id = assets.id WHERE schedule_id = ? AND date = ? ORDER BY params", (block[0], date)).fetchone()[0]
		if timesum is None:
			timesum = 0
		times.append(int((datetime.strptime(block[2], "%H:%M")-datetime.strptime(block[1], "%H:%M")).total_seconds()) - timesum)
	db.close()
	return render_template("music.html", blocks=enumerate(blocks), music=music, date=date, times=times)

@app.route("/viewmusic/<string:date>/add/<int:schedule_id>", methods=("GET", "POST"))
@login_required
@permission_required("setmusic")
def addmusic(date, schedule_id):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	if request.method == "POST":
		params = cursor.execute("SELECT MAX(params) FROM customsounds WHERE date = ? AND schedule_id = ?", (date, schedule_id)).fetchone()
		param = 0
		if params[0] != None:
			param = int(params[0])+1
		cursor.execute("INSERT INTO customsounds(asset_id, date, schedule_id, params) VALUES (?, ?, ?, ?)", (request.form.get("file"), date, schedule_id, param))
		db.commit()
		db.close()
		flash("Zene sikeresen hozzáadva!", "success")
		return redirect(url_for("viewmusic", date=date))
	files = cursor.execute("SELECT id, filepath FROM assets WHERE asset_type = 2").fetchall()
	db.close()
	return render_template("addmusic.html", files=files)

@app.route("/viewmusic/<string:date>/delete/<int:id>")
@login_required
@permission_required("setmusic")
def deletemusic(id, date):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	cursor.execute("DELETE FROM customsounds WHERE id = ?", (id, ))
	db.commit()
	db.close()
	flash("Sikeres törlés!", "success")
	return redirect(url_for("viewmusic", date=date))

@app.route("/listplaybacks")
@login_required
@permission_required("playbacks")
def listplaybacks():
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	playbacks = cursor.execute("SELECT playbacks.id, assets.filepath, playbacks.date, playbacks.time FROM playbacks INNER JOIN assets ON playbacks.asset_id = assets.id ORDER BY playbacks.date, playbacks.time").fetchall()
	db.close()
	return render_template("listplaybacks.html", playbacks=playbacks)

@app.route("/deleteplayback/<int:id>")
@login_required
@permission_required("playbacks")
def deleteplayback(id):
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	cursor.execute("DELETE FROM playbacks WHERE id = ?", (id, ))
	db.commit()
	db.close()
	flash("Sikeres törlés!", "success")
	return redirect(url_for("listplaybacks"))

@app.route("/addplayback", methods=("GET", "POST"))
@login_required
@permission_required("playbacks")
def addplayback():
	if request.method == "POST":
		date = request.form.get("date")
		time = request.form.get("time")
		assetid = request.form.get("file")
		db = sqlite3.connect(settings["programmesDb"])
		cursor = db.cursor()
		cursor.execute("INSERT INTO playbacks (asset_id, date, time) VALUES (?, ?, ?)", (assetid, date, time))
		db.commit()
		db.close()
		flash("Sikeres hozzáadás!", "success")
		if date == datetime.now().strftime("%Y-%m-%d"):
			flash(Markup("Mivel a mai dátumra adott hozzá egy bejátszást, ezért <a href='" + url_for('reload') + "'>újra kell tölteni</a> a mai napot a módosítások érvényesítéséhez. <br><i>Figyelem! Újratöltést <b>csak akkor szabad végezni, amikor éppen nem szól semmi</b>, hiszen ha a csengetés percében töltjük újra a mai programot, akkor az adott percre vonatkozó csengetések, bejátszások <b>újra meg fognak szólalni!</b></i>"), "info")
		return redirect(url_for("listplaybacks"))
	db = sqlite3.connect(settings["programmesDb"])
	cursor = db.cursor()
	files = cursor.execute("SELECT id, filepath FROM assets").fetchall()
	db.close()
	return render_template("addplayback.html", files=files)

@app.route("/register", methods=("GET", "POST"))
@login_required
@permission_required("createusers")
def register():
	db = sqlite3.connect(settings["usersDb"])
	cursor = db.cursor()
	permissions = cursor.execute("SELECT id, humanname FROM permissions INNER JOIN userpermissions ON id = permission_id WHERE user_id = ? ORDER BY humanname", (current_user.id, )).fetchall()
	db.close()
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
			userid = cursor.execute("SELECT id FROM users WHERE username = ?", (name, )).fetchone()
			for permission in permissions:
				if request.form.get("permission"+str(permission[0])) == '1':
					cursor.execute("INSERT INTO userpermissions (user_id, permission_id) VALUES (?, ?)", (userid[0], permission[0]))
			db.commit()
			flash("Felhasználó sikeresen létrehozva!", "success")
			db.close()
			return redirect(url_for("listusers"))
		else:
			flash("A két jelszó nem egyezik!", "danger")
	return render_template("register.html", permissions=permissions)

@app.route("/editpermissions/<int:id>", methods=("GET", "POST"))
@login_required
@permission_required("editpermissions")
def editpermissions(id):
	db = sqlite3.connect(settings["usersDb"])
	cursor = db.cursor()
	username = cursor.execute("SELECT username FROM users WHERE id = ?", (id, )).fetchone()
	permissions = cursor.execute("SELECT id, humanname FROM permissions INNER JOIN userpermissions ON id = permission_id WHERE user_id = ? ORDER BY humanname", (current_user.id, )).fetchall()
	userpermissions = cursor.execute("SELECT permission_id FROM userpermissions WHERE user_id = ?", (id, )).fetchall()
	if request.method == "POST":
		for permission in permissions:
			if request.form.get("permission"+str(permission[0])) == '1':
				result = cursor.execute("SELECT COUNT(*) FROM userpermissions WHERE user_id = ? AND permission_id = ?", (id, permission[0])).fetchone()
				if result[0] == 0:
					cursor.execute("INSERT INTO userpermissions (user_id, permission_id) VALUES (?, ?)", (id, permission[0]))
			elif request.form.get("permission"+str(permission[0])) == '0':
				cursor.execute("DELETE FROM userpermissions WHERE user_id = ? AND permission_id = ?", (id, permission[0]))
		db.commit()
		flash("Sikeres módosítás!", "success")
		db.close()
		return redirect(url_for("listusers"))
	db.close()
	return render_template("editpermissions.html", permissions=permissions, userpermissions=userpermissions, username=username[0])

@app.route("/listusers")
@login_required
@permission_required("listusers")
def listusers():
	db = sqlite3.connect(settings["usersDb"])
	cursor = db.cursor()
	result = cursor.execute("SELECT id, username FROM users").fetchall()
	db.close()
	return render_template("listusers.html", users=result)

@app.route("/deleteuser/<int:id>")
@login_required
@permission_required("deleteusers")
def deleteuser(id):
	db = sqlite3.connect(settings["usersDb"])
	cursor = db.cursor()
	cursor.execute("DELETE FROM users WHERE id = ?", (id,))
	cursor.execute("DELETE FROM userpermissions WHERE user_id = ?", (id, ))
	db.commit()
	flash("Felhasználó sikeresen törölve!", "success")
	db.close()
	return redirect(url_for("listusers"))

@app.route("/settings", methods=("GET", "POST"))
@login_required
@permission_required("editsettings")
def settings():
	if request.method == "POST":
		for setting in list(settings.keys()):
			if request.form.get(setting) is not None:
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
thread.daemon = True
thread.start()
while True:
	time = datetime.now()
	if lastloaded != time.day:
		loadTodaysProgramme()
	for event in events:
		if event.time.hour == time.hour and event.time.minute == time.minute and isinstance(event, (SoundEvent, MusicEvent)):
			if isinstance(event, MusicEvent) and musicEnabled == False:
				events.remove(event)
				continue
			if isinstance(event, MusicEvent) and (pygame.mixer.Channel(1).get_busy() == True or pygame.mixer.Channel(0).get_busy() == True):
				continue
			if not isinstance(event, MusicEvent):
				if event.type == 1 and bellEnabled == False:
					events.remove(event)
					continue
				if event.type == 2 and customplaybackEnabled == False:
					events.remove(event)
					continue
				if event.type == 1 and pygame.mixer.Channel(1).get_busy() == True:
					continue
			event.play()
			events.remove(event)
		if time.time().replace(microsecond=0) == event.time.time() and isinstance(event, MusicFadeEvent):
			event.play()
			events.remove(event)
	if pygame.mixer.music.get_busy():
		if musicpos > pygame.mixer.music.get_pos() and music != []:
			pygame.mixer.music.queue(music.pop())
		musicpos = pygame.mixer.music.get_pos()
	sleep(0.2)
