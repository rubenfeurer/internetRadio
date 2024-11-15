import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict

class AlsaFilter(logging.Filter):
    """Filter out ALSA-related messages"""
    def filter(self, record):
        if hasattr(record, 'msg'):
            patterns = [
                "snd_use_case_mgr_open",
                "failed to import hw:",
                "Could not unmute Master",
                "Unable to find simple control",
                "Could not set Master volume",
                "Warning: Could not",
                "amixer: Unable to find",
                "alsa-lib"
            ]
            return not any(pattern in str(record.msg) for pattern in patterns)
        return True

class Logger:
    _instances = {}
    
    def __init__(self, name):
        """Initialize logger with specific settings for size control"""
        if name not in Logger._instances:
            self.logger = logging.getLogger(name)
            self.logger.setLevel(logging.INFO)
            self._configure_logger(name)
            Logger._instances[name] = self.logger
        else:
            self.logger = Logger._instances[name]

    def _configure_logger(self, name):
        """Configure logger with strict size limits"""
        # Set very conservative size limits
        MAX_BYTES = 1024 * 1024  # 1MB
        BACKUP_COUNT = 2  # Keep only 2 backup files
        
        # Map logger names to their log files
        log_files = {
            'radio': 'radio.log',
            'network': 'wifi.log',
            'app': 'app.log'
        }
        
        # Get log file name or use default
        log_file = log_files.get(name, f'{name}.log')
        log_path = os.path.join(os.getcwd(), 'logs', log_file)
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        # Configure rotating file handler with strict limits
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        
        # Set format to include minimal necessary information
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message).200s',  # Limit message length
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Only log INFO and above to file
        file_handler.setLevel(logging.INFO)
        
        # Configure console output only in development
        if 'DEVELOPMENT' in os.environ:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        self.logger.addHandler(file_handler)

    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def debug(self, msg: str):
        self.logger.debug(msg)