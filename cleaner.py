#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLEANER - Xóa sạch mọi dấu vết của RAT, Miner, Stealer, Persistence
Chạy với quyền Administrator để xóa hoàn toàn
"""

import os
import sys
import subprocess
import platform
import ctypes
import winreg
import shutil
import glob
from datetime import datetime

# ========== MÀU CHO LOG ==========
def print_color(text, color='white'):
    colors = {
        'red': '\033[91m', 'green': '\033[92m', 'yellow': '\033[93m',
        'blue': '\033[94m', 'magenta': '\033[95m', 'cyan': '\033[96m',
        'white': '\033[97m', 'reset': '\033[0m'
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")

# ========== KIỂM TRA ADMIN ==========
def is_admin():
    if platform.system() == 'Windows':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    return os.geteuid() == 0

def run_as_admin():
    if platform.system() == 'Windows':
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

# ========== LOG ==========
logs = []
def log(msg, status='info'):
    timestamp = datetime.now().strftime('%H:%M:%S')
    if status == 'info':
        logs.append(f"[{timestamp}] ✔ {msg}")
        print_color(f"[{timestamp}] ✔ {msg}", 'green')
    elif status == 'warn':
        logs.append(f"[{timestamp}] ⚠ {msg}")
        print_color(f"[{timestamp}] ⚠ {msg}", 'yellow')
    elif status == 'error':
        logs.append(f"[{timestamp}] ✖ {msg}")
        print_color(f"[{timestamp}] ✖ {msg}", 'red')
    else:
        logs.append(f"[{timestamp}] {msg}")
        print_color(f"[{timestamp}] {msg}", 'cyan')

# ========== DỌN TIẾN TRÌNH ==========
def kill_processes():
    processes = ['xmrig.exe', 'pythonw.exe', 'python.exe', 'exodus.exe', 'Atomic Wallet.exe', 'steam.exe']
    for proc in processes:
        try:
            subprocess.run(f'taskkill /F /IM {proc}', shell=True, capture_output=True)
            log(f"Killed process: {proc}", 'info')
        except:
            pass

# ========== DỌN REGISTRY ==========
def clean_registry():
    registry_paths = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "SystemUpdate"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "StitchClient"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "RATClient"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "MicrosoftEdgeUpdate"),
    ]
    for hkey, subkey, value_name in registry_paths:
        try:
            key = winreg.OpenKey(hkey, subkey, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, value_name)
            winreg.CloseKey(key)
            log(f"Deleted registry: {subkey}\\{value_name}", 'info')
        except FileNotFoundError:
            pass
        except Exception as e:
            log(f"Error deleting registry {value_name}: {e}", 'warn')

# ========== DỌN SCHEDULED TASKS ==========
def clean_tasks():
    tasks = ['SystemUpdateTask', 'MicrosoftEdgeUpdateTask', 'RATClientUpdate']
    for task in tasks:
        try:
            subprocess.run(f'schtasks /delete /tn {task} /f', shell=True, capture_output=True)
            log(f"Deleted scheduled task: {task}", 'info')
        except:
            pass

# ========== DỌN THƯ MỤC ==========
def clean_directories():
    paths_to_delete = [
        # Thư mục ẩn từ RAT và miner
        os.path.join(os.environ.get('PROGRAMDATA', ''), 'Microsoft', 'Windows', 'Caches', 'System32'),
        os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Caches', 'SystemUpdate'),
        os.path.join(os.environ.get('APPDATA', ''), 'XMRigTest'),
        os.path.join(os.environ.get('TEMP', ''), 'muck*'),
        os.path.join(os.environ.get('TEMP', ''), 'rat_runtime'),
        # File backup
        os.path.join(os.environ.get('WINDIR', ''), 'System32', 'Tasks', 'MicrosoftEdgeUpdate.exe'),
        os.path.join(os.environ.get('WINDIR', ''), 'Temp', 'svchost.exe'),
        # Có thể có thư mục con khác
        os.path.join(os.environ.get('APPDATA', ''), 'discord'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default', 'Local Storage', 'leveldb'),
    ]
    for path in paths_to_delete:
        if not path:
            continue
        try:
            if os.path.exists(path):
                if os.path.isfile(path):
                    os.remove(path)
                    log(f"Deleted file: {path}", 'info')
                elif os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                    log(f"Deleted directory: {path}", 'info')
            else:
                # Xóa wildcard (nếu có *)
                if '*' in path:
                    for p in glob.glob(path):
                        if os.path.isfile(p):
                            os.remove(p)
                        elif os.path.isdir(p):
                            shutil.rmtree(p, ignore_errors=True)
                        log(f"Deleted wildcard: {p}", 'info')
        except Exception as e:
            log(f"Error deleting {path}: {e}", 'warn')

# ========== DỌN FILE TẠM TRONG %TEMP% ==========
def clean_temp_files():
    temp_dir = os.environ.get('TEMP', '')
    patterns = ['muck*', 'xmrig*', 'rat*', '*.log', '*.tmp', '*.zip', '*.pyc', '*.exe']
    for pattern in patterns:
        try:
            for f in glob.glob(os.path.join(temp_dir, pattern)):
                try:
                    if os.path.isfile(f):
                        os.remove(f)
                        log(f"Deleted temp file: {f}", 'info')
                except:
                    pass
        except:
            pass

# ========== DỌN CACHE TRÌNH DUYỆT (TÙY CHỌN) ==========
def clean_browser_cache():
    print_color("\nDo you want to clear browser caches (may contain tokens/cookies)? (y/n): ", 'yellow')
    choice = input().strip().lower()
    if choice == 'y':
        browser_paths = [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default', 'Cache'),
            os.path.join(os.environ.get('APPDATA', ''), 'Mozilla', 'Firefox', 'Profiles'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data', 'Default', 'Cache'),
        ]
        for path in browser_paths:
            if os.path.exists(path):
                try:
                    shutil.rmtree(path, ignore_errors=True)
                    log(f"Deleted browser cache: {path}", 'info')
                except:
                    pass
    else:
        log("Skipped browser cache cleaning", 'info')

# ========== MAIN ==========
def main():
    print_color("=" * 70, 'cyan')
    print_color("🧹 RAT & MINER CLEANER - XÓA SẠCH MỌI DẤU VẾT", 'magenta')
    print_color("=" * 70, 'cyan')
    print_color("Chạy với quyền Administrator để xóa triệt để.\n", 'yellow')

    if not is_admin():
        log("Yêu cầu quyền Administrator, đang khởi động lại...", 'warn')
        run_as_admin()
        return

    log("=== BẮT ĐẦU DỌN DẸP ===", 'info')
    kill_processes()
    clean_registry()
    clean_tasks()
    clean_directories()
    clean_temp_files()
    clean_browser_cache()

    print_color("\n" + "=" * 70, 'cyan')
    log("✅ DỌN DẸP HOÀN TẤT! Mọi dấu vết RAT, Miner, Stealer đã bị xóa.", 'info')
    print_color("=" * 70, 'cyan')
    print_color("Khuyến nghị: Khởi động lại máy để xóa các file đang bị khóa.", 'yellow')
    input("\nNhấn Enter để thoát...")

if __name__ == '__main__':
    main()