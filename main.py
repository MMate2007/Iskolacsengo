import json
import pygame
import time

pygame.init()

with open("settings.json") as f:
	settings = json.load(f)
	
with open(settings["programmeFilePath"]) as p:
	programmes = json.load(p)
	for prog in programmes:
		prog["time"] = time.strptime(prog["time"], "%H:%M")
		
while True:
	for prog in programmes:
		if prog["time"].tm_hour == time.localtime().tm_hour and prog["time"].tm_min == time.localtime().tm_min:
			pygame.mixer.Sound(prog["file"]).play()
			programmes.remove(prog)
	time.sleep(0.2)
