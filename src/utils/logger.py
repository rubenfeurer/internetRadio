import logging
from logging.handlers import RotatingFileHandler
import os

class Logger:
    _instances = {}

    def __new__(cls, name, log_dir=None):
        if name not in cls._instances:
            instance = super(Logger, cls).__new__(cls)
            cls._instances[name] = instance
            try:
                instance.__init__(name, log_dir)
            except Exception as e:
                print(f"Warning: Failed to initialize file logger: {e}")
                # Create a simple console logger as fallback
                logger = logging.getLogger(name)
                logger.setLevel(logging.INFO)
                
                # Add console handler if none exists
                if not logger.handlers:
                    console_handler = logging.StreamHandler()
                    console_handler.setLevel(logging.INFO)
                    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                    console_handler.setFormatter(formatter)
                    logger.addHandler(console_handler)
                
                cls._instances[name] = logger
                return logger
                
        return cls._instances[name]

    def __init__(self, name, log_dir=None):
        """Initialize logger with file and console handlers"""
        if not hasattr(self, '_logger'):  # Only initialize once
            self._logger = logging.getLogger(name)
            self._logger.setLevel(logging.INFO)
            
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            
            # Add console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)
            
            # Add file handler if log_dir is provided
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, f'{name}.log')
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=1024*1024,  # 1MB
                    backupCount=5
                )
                file_handler.setLevel(logging.INFO)
                file_handler.setFormatter(formatter)
                self._logger.addHandler(file_handler)

    def info(self, msg):
        """Log info message"""
        if hasattr(self, '_logger'):
            self._logger.info(msg)
        else:
            self.info(msg)  # For fallback logger

    def error(self, msg):
        """Log error message"""
        if hasattr(self, '_logger'):
            self._logger.error(msg)
        else:
            self.error(msg)  # For fallback logger

    def warning(self, msg):
        """Log warning message"""
        if hasattr(self, '_logger'):
            self._logger.warning(msg)
        else:
            self.warning(msg)  # For fallback logger

    def debug(self, msg):
        """Log debug message"""
        if hasattr(self, '_logger'):
            self._logger.debug(msg)
        else:
            self.debug(msg)  # For fallback logger

    @classmethod
    def cleanup(cls):
        """Clean up all handlers"""
        for name, instance in cls._instances.items():
            if hasattr(instance, '_logger'):
                for handler in instance._logger.handlers[:]:
                    handler.close()
                    instance._logger.removeHandler(handler)
        cls._instances.clear()