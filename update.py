from imexport import export, importfromfile
import sys
import shutil
import os
from datetime import datetime

export(sys.argv[1], "updateexport.json")
backup = "../Iskolacsengo-backup-"+datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copytree("./", backup)
os.system("git pull")
os.system("python initdbs.py")
importfromfile("updateexport.json")
os.remove("updateexport.json")
shutil.rmtree("__pycache__")
os.system("systemctl restart iskolacsengo.service")
if os.system("service iskolacsengo status") != 0:
    # Cserélje vissza a backupra