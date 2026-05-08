# core/encryption.py
import base64
import hashlib
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class AESCipher:
    def __init__(self, key: str):
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, plaintext: str) -> str:
        iv = os.urandom(16)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
        combined = iv + encrypted
        return base64.b64encode(combined).decode()

    def decrypt(self, ciphertext_b64: str) -> str:
        combined = base64.b64decode(ciphertext_b64)
        iv = combined[:16]
        encrypted = combined[16:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
        return decrypted.decode()

# Simple XOR obfuscation for strings
class XORObfuscator:
    @staticmethod
    def obfuscate(data: str, key: str = "stitch") -> str:
        result = []
        key_bytes = key.encode()
        for i, ch in enumerate(data.encode()):
            result.append(ch ^ key_bytes[i % len(key_bytes)])
        return base64.b64encode(bytes(result)).decode()

    @staticmethod
    def deobfuscate(data_b64: str, key: str = "stitch") -> str:
        decoded = base64.b64decode(data_b64)
        key_bytes = key.encode()
        result = []
        for i, byte in enumerate(decoded):
            result.append(byte ^ key_bytes[i % len(key_bytes)])
        return bytes(result).decode()
