import sqlite3
import json
import pygame
from datetime import datetime, timedelta
from time import sleep

pygame.init()
with open("settings.json") as f:
		settings = json.load(f)

events = []

class SoundEvent():
	def __init__(self, time, sound, volume = 1):
		self.time = time
		self.sound = sound
		self.volume = volume
		if volume is None:
			self.volume = 1
	def play(self):
		pygame.mixer.Channel(0).set_volume(self.volume)
		pygame.mixer.Channel(0).play(pygame.mixer.Sound(self.sound))

def readSettings():
	with open("settings.json") as f:
		settings = json.load(f)

def loadTodaysProgramme():
	loaddb = sqlite3.connect(settings["programmesDb"])
	loadcursor = loaddb.cursor()
	qresult = loadcursor.execute("SELECT pattern_id FROM dates WHERE date = DATE('now', 'localtime')").fetchone()
	if qresult is None:
		return
	patternid = qresult[0]
	results = loadcursor.execute("SELECT schedule_type, start, end, asset_id FROM schedule WHERE pattern_id = ? ORDER BY id", (patternid,)).fetchall()
	for result in results:
		if result[0] == 1:
			assetresult = loadcursor.execute("SELECT filepath, volume FROM assets WHERE id = ?", (settings["classStartAssetId"],)).fetchone()
			events.append(SoundEvent(datetime.strptime(result[1], "%H:%M"), assetresult[0], assetresult[1]))
			assetresult = loadcursor.execute("SELECT filepath, volume FROM assets WHERE id = ?", (settings["classEndReminderAssetId"],)).fetchone()
			events.append(SoundEvent(datetime.strptime(result[2], "%H:%M")-timedelta(minutes=settings["classEndReminderMin"]), assetresult[0], assetresult[1]))
			assetresult = loadcursor.execute("SELECT filepath, volume FROM assets WHERE id = ?", (settings["classEndAssetId"],)).fetchone()
			events.append(SoundEvent(datetime.strptime(result[2], "%H:%M"), assetresult[0], assetresult[1]))

readSettings()
loadTodaysProgramme()

while True:
	for event in events:
		if event.time.hour == datetime.now().hour and event.time.minute == datetime.now().minute:
			event.play()
			events.remove(event)
	sleep(0.2)
