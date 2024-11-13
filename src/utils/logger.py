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
    def setup_logging(cls, log_dir: str, level: str = "INFO") -> None:
        """Set up logging configuration"""
        if cls._initialized:
            cls.reset()

        os.makedirs(log_dir, exist_ok=True)
        cls._log_dir = log_dir
        
        # Set up formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Create and configure handlers
        file_handlers = {
            'app': os.path.join(log_dir, 'app.log'),
            'radio': os.path.join(log_dir, 'radio.log'),
            'wifi': os.path.join(log_dir, 'wifi.log')
        }

        # Create handlers and set formatter
        for name, path in file_handlers.items():
            handler = logging.FileHandler(path, mode='w')  # Use 'w' mode to clear file
            handler.setFormatter(formatter)
            cls._handlers[name] = handler

        # Set up root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level.upper()))
        
        # Add handlers to root logger
        for handler in cls._handlers.values():
            if handler not in root_logger.handlers:
                root_logger.addHandler(handler)
        
        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger instance"""
        if not cls._initialized:
            cls.setup_logging(cls._log_dir or os.path.join(os.getcwd(), 'logs'))
        
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            logger.propagate = True  # Ensure messages propagate to root logger
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