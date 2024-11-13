import logging
import os
from typing import Optional, Dict

class Logger:
    _instance = None
    _initialized = False
    _test_mode = False
    _log_dir = None
    _loggers: Dict[str, logging.Logger] = {}
    _handlers: Dict[str, logging.Handler] = {}

    def __new__(cls, name: str = None):
        """Handle singleton pattern and logger creation"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            
        if name:
            # Return existing logger if available
            if name in cls._loggers:
                return cls._loggers[name]
            
            # Create new logger if needed
            if not cls._initialized:
                cls.setup_logging(cls._log_dir or os.path.join(os.getcwd(), 'logs'))
            logger = cls.get_logger(name)
            cls._loggers[name] = logger
            return cls._instance
            
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset logger state for testing"""
        # Remove all handlers from root logger
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
            handler.close()

        # Remove handlers from individual loggers
        for logger in cls._loggers.values():
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                handler.close()

        # Clear class variables
        cls._instance = None
        cls._initialized = False
        cls._test_mode = False
        cls._log_dir = None
        cls._loggers.clear()
        cls._handlers.clear()

        # Reset root logger
        logging.getLogger().setLevel(logging.INFO)

    @classmethod
    def setup_logging(cls, log_dir: str = None, app_log_path: str = None, network_log_path: str = None, level: str = "DEBUG") -> None:
        """Set up logging configuration"""
        cls.reset()
        
        # Determine log directory
        if app_log_path:
            log_dir = os.path.dirname(app_log_path)
        elif log_dir is None:
            log_dir = os.path.join(os.getcwd(), 'logs')
        
        os.makedirs(log_dir, exist_ok=True)
        cls._log_dir = log_dir
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create handlers with proper log levels
        handlers = {
            'app': (app_log_path or os.path.join(log_dir, 'app.log'), logging.DEBUG),
            'radio': (os.path.join(log_dir, 'radio.log'), logging.INFO),
            'wifi': (network_log_path or os.path.join(log_dir, 'wifi.log'), logging.INFO)
        }
        
        for name, (path, log_level) in handlers.items():
            handler = logging.FileHandler(path)
            handler.setFormatter(formatter)
            handler.setLevel(log_level)
            cls._handlers[name] = handler
        
        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger instance"""
        if not cls._initialized:
            cls.setup_logging(cls._log_dir or os.path.join(os.getcwd(), 'logs'))
        
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(logging.DEBUG)
            
            # Add handlers if not already added
            for handler in cls._handlers.values():
                if handler not in logger.handlers:
                    logger.addHandler(handler)
            
            cls._loggers[name] = logger
        
        return cls._loggers[name]

    @classmethod
    def set_level(cls, level: str) -> None:
        """Set logging level"""
        log_level = getattr(logging, level.upper())
        
        # Set root logger level
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Set level for all handlers
        for handler in cls._handlers.values():
            handler.setLevel(log_level)