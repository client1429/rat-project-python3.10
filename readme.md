# Stitch RAT Framework

Educational RAT with stealer, miner, persistence, and web GUI.

## Features
- Remote shell, screenshot, keylogger
- XMRig miner auto-install
- Chromium & Firefox stealer (passwords, cookies, cards)
- Advanced persistence (registry, scheduled tasks, WMI, service)
- Telegram C2 channel
- AES encryption
- Remote desktop streaming
- File browser
- Plugin system
- Web admin panel (Flask + SocketIO)

## Quick Start
```bash
pip install -r requirements.txt
# Edit core/config.py with your IP and key
python run1.py -server -key YOUR_KEY
# Web panel: python web_gui.py -key YOUR_KEY
```

See full documentation at https://github.com/yourusername/Stitch
