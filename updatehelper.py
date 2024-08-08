import os
from shutil import rmtree
from imexport import importfromfile

os.system("systemctl stop iskolacsengo.service")
os.system("git pull")
os.system("python initdbs.py")
importfromfile("updateexport.json")
os.remove("updateexport.json")
rmtree("__pycache__")
os.system("systemctl start iskolacsengo.service")