#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import ctypes
import winreg
import shutil
import glob
from datetime import datetime

def print_color(text, color='white'):
    colors = {
        'red': '\033[91m', 'green': '\033[92m', 'yellow': '\033[93m',
        'blue': '\033[94m', 'magenta': '\033[95m', 'cyan': '\033[96m',
        'white': '\033[97m', 'reset': '\033[0m'
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")

def log(msg, status='info'):
    timestamp = datetime.now().strftime('%H:%M:%S')
    if status == 'info':
        print_color(f"[{timestamp}] ✔ {msg}", 'green')
    elif status == 'warn':
        print_color(f"[{timestamp}] ⚠ {msg}", 'yellow')
    elif status == 'error':
        print_color(f"[{timestamp}] ✖ {msg}", 'red')
    else:
        print_color(f"[{timestamp}] {msg}", 'cyan')

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

def kill_processes():
    processes = ['xmrig.exe', 'pythonw.exe', 'python.exe']
    for proc in processes:
        try:
            subprocess.run(f'taskkill /F /IM {proc}', shell=True, capture_output=True)
            log(f"Killed {proc}")
        except:
            pass

def clean_registry():
    registry_paths = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "SystemUpdate"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "StitchClient"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "RATClient"),
    ]
    for hkey, subkey, value_name in registry_paths:
        try:
            key = winreg.OpenKey(hkey, subkey, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, value_name)
            winreg.CloseKey(key)
            log(f"Deleted registry: {subkey}\\{value_name}")
        except:
            pass

def clean_tasks():
    tasks = ['SystemUpdateTask', 'MicrosoftEdgeUpdateTask', 'RATClientUpdate']
    for task in tasks:
        try:
            subprocess.run(f'schtasks /delete /tn {task} /f', shell=True, capture_output=True)
            log(f"Deleted task: {task}")
        except:
            pass

def clean_directories():
    paths = [
        os.path.join(os.environ.get('PROGRAMDATA', ''), 'Microsoft', 'Windows', 'Caches', 'System32'),
        os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Caches', 'SystemUpdate'),
        os.path.join(os.environ.get('APPDATA', ''), 'XMRigTest'),
        os.path.join(os.environ.get('WINDIR', ''), 'System32', 'Tasks', 'MicrosoftEdgeUpdate.exe'),
        os.path.join(os.environ.get('WINDIR', ''), 'Temp', 'svchost.exe'),
    ]
    for path in paths:
        if path and os.path.exists(path):
            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path, ignore_errors=True)
                log(f"Deleted: {path}")
            except Exception as e:
                log(f"Error deleting {path}: {e}", 'error')
    temp_dir = os.environ.get('TEMP', '')
    patterns = ['muck*', 'xmrig*', 'rat*']
    for pattern in patterns:
        for f in glob.glob(os.path.join(temp_dir, pattern)):
            try:
                os.remove(f)
                log(f"Deleted temp: {f}")
            except:
                pass

def main():
    print_color("=" * 70, 'cyan')
    print_color("🧹 RAT & MINER CLEANER - XÓA SẠCH MỌI DẤU VẾT", 'magenta')
    print_color("=" * 70, 'cyan')
    if not is_admin():
        log("Requesting admin privileges...", 'warn')
        run_as_admin()
        return
    kill_processes()
    clean_registry()
    clean_tasks()
    clean_directories()
    print_color("\n✅ Cleanup completed. Please reboot to ensure all files are removed.", 'green')
    input("Press Enter to exit...")

if __name__ == '__main__':
    main()