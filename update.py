from imexport import export, importfromfile
import sys
import shutil
import os
from datetime import datetime
from time import sleep

backup = "../Iskolacsengo-backup-"+datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copytree("./", backup)
export(sys.argv[1], "updateexport.json")
os.system("git pull")
os.system("python initdbs.py")
importfromfile("updateexport.json")
os.remove("updateexport.json")
shutil.rmtree("__pycache__")
os.system("systemctl restart iskolacsengo.service")
sleep(3)
if os.system("service iskolacsengo status") != 0:
    print("Visszacserélés a korábbi verzióra...")
    shutil.copytree(backup, "./", dirs_exist_ok=True)
    os.system("systemctl restart iskolacsengo.service")
else:
    print("Sikeres frissítés!")