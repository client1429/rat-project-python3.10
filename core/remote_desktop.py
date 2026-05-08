# core/remote_desktop.py
import mss
import numpy as np
import zlib
import base64
import threading
import time
import socket
from typing import Callable, Optional

class RemoteDesktopStreamer:
    """Stream screen captures to server"""
    def __init__(self, quality: int = 50, fps: int = 5):
        self.quality = quality  # Not used directly but for future JPEG compression
        self.fps = fps
        self.running = False
        self.callback = None
        self.sct = mss.mss()
        
    def capture_screen(self) -> bytes:
        """Capture screen and return compressed PNG bytes"""
        try:
            monitor = self.sct.monitors[1]  # Primary monitor
            screenshot = self.sct.grab(monitor)
            # Convert to RGB and compress
            img_bytes = bytes(screenshot.rgb)
            compressed = zlib.compress(img_bytes, level=6)
            return compressed
        except Exception as e:
            print(f"Capture error: {e}")
            return b''
            
    def start_streaming(self, callback: Callable[[bytes], None]):
        """Start streaming frames to callback"""
        self.running = True
        self.callback = callback
        interval = 1.0 / self.fps
        
        def stream():
            while self.running:
                start = time.time()
                frame = self.capture_screen()
                if frame and self.callback:
                    self.callback(frame)
                elapsed = time.time() - start
                if elapsed < interval:
                    time.sleep(interval - elapsed)
        
        thread = threading.Thread(target=stream, daemon=True)
        thread.start()
        
    def stop_streaming(self):
        """Stop streaming"""
        self.running = False

def send_frame_to_server(sock: socket.socket, frame: bytes):
    """Helper to send frame over socket with length prefix"""
    try:
        from core.helpers import send_msg
        b64_frame = base64.b64encode(frame).decode()
        send_msg(sock, f"STREAM:{b64_frame}")
    except Exception as e:
        print(f"Stream send error: {e}")

class RemoteDesktopServer:
    """Server side to receive and display frames"""
    def __init__(self):
        self.frames = []
        
    def process_frame(self, b64_frame: str) -> Optional[bytes]:
        """Decode and decompress frame"""
        try:
            compressed = base64.b64decode(b64_frame)
            decompressed = zlib.decompress(compressed)
            return decompressed
        except:
            return None
            
    def save_frame_as_image(self, b64_frame: str, output_path: str):
        """Save frame as PNG"""
        data = self.process_frame(b64_frame)
        if data:
            from PIL import Image
            import io
            # Convert raw RGB to image
            # Note: need width/height; we'll store metadata separately in real implementation
            pil_img = Image.frombytes('RGB', (1920, 1080), data)
            pil_img.save(output_path)
            return True
        return False
