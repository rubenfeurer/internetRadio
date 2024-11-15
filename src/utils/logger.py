import logging
import os
from logging.handlers import RotatingFileHandler

class Logger:
    _instances = {}
    _handlers = set()  # Track all handlers
    
    def __new__(cls, name, log_dir=None):
        key = f"{name}:{log_dir}"
        if key not in cls._instances:
            instance = super().__new__(cls)
            instance.__init__(name, log_dir)
            cls._instances[key] = instance
        return cls._instances[key]
    
    def __init__(self, name, log_dir=None):
        if not hasattr(self, '_initialized'):
            self.logger = logging.getLogger(name)
            self.logger.setLevel(logging.INFO)
            
            # Use provided log_dir or default to 'logs'
            self.log_dir = log_dir or os.path.join(os.getcwd(), 'logs')
            os.makedirs(self.log_dir, exist_ok=True)
            
            # Remove existing handlers if any
            self._remove_existing_handlers()
            
            # File handler
            log_file = os.path.join(self.log_dir, f'{name}.log')
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=1024 * 1024,  # 1MB
                backupCount=3
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(file_handler)
            self._handlers.add(file_handler)  # Track handler
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(levelname)s: %(message)s'
            ))
            self.logger.addHandler(console_handler)
            self._handlers.add(console_handler)  # Track handler
            
            self._initialized = True
    
    def _remove_existing_handlers(self):
        """Remove and close existing handlers"""
        if hasattr(self, 'logger'):
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)
                if handler in self._handlers:
                    self._handlers.remove(handler)
    
    @classmethod
    def cleanup(cls):
        """Clean up all resources"""
        # Close all handlers
        for handler in cls._handlers.copy():
            try:
                handler.close()
            except:
                pass  # Ignore errors during cleanup
        cls._handlers.clear()
        
        # Clear instances and remove handlers
        for instance in cls._instances.values():
            if hasattr(instance, 'logger'):
                instance._remove_existing_handlers()
        cls._instances.clear()
        
        # Clear logging configuration
        logging.Logger.manager.loggerDict.clear()
    
    def info(self, message):
        self.logger.info(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def debug(self, message):
        self.logger.debug(message)
    
    def warning(self, message):
        self.logger.warning(message)