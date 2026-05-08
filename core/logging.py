# core/logging.py
import logging
import os
import sys
from datetime import datetime
from typing import Optional

class Logger:
    """Centralized logging with file and console output"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.log_dir = os.path.join(os.environ.get('APPDATA', os.getcwd()), 'StitchLogs')
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.logger = logging.getLogger('StitchRAT')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler for errors
        error_log = os.path.join(self.log_dir, f'error_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(error_log)
        file_handler.setLevel(logging.ERROR)
        file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
        
        # Console handler for info
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
    def info(self, msg: str):
        self.logger.info(msg)
        
    def error(self, msg: str):
        self.logger.error(msg)
        
    def debug(self, msg: str):
        self.logger.debug(msg)
        
    def warning(self, msg: str):
        self.logger.warning(msg)
        
    def log_exception(self, e: Exception, context: str = ""):
        import traceback
        tb = traceback.format_exc()
        self.error(f"Exception in {context}: {e}\n{tb}")

def get_logger() -> Logger:
    return Logger()
