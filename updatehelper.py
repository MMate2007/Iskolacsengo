import os
import sys
from shutil import rmtree
from imexport import importfromfile, export

export(sys.argv[1], "updateexport.json")
os.system("git pull")
os.system("python initdbs.py")
importfromfile("updateexport.json")
os.remove("updateexport.json")
rmtree("__pycache__")