import os
import logging
from pathlib import Path
from typing import Optional

class Logger:
    _instance = None
    _initialized = False
    _test_mode = False
    _test_log_dir = None

    def __new__(cls, name: str = None):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self, name: str = None):
        if not Logger._initialized:
            self.setup_logging()
            Logger._initialized = True
        
        self.logger = logging.getLogger(name if name else __name__)

    @classmethod
    def set_test_mode(cls, test_log_dir: str):
        """Enable test mode with custom log directory"""
        cls._test_mode = True
        cls._test_log_dir = test_log_dir
        cls._initialized = False
        cls._instance = None  # Reset instance for test

    @classmethod
    def reset(cls):
        """Reset logger state - useful between tests"""
        cls._instance = None
        cls._initialized = False
        cls._test_mode = False
        cls._test_log_dir = None

    @staticmethod
    def setup_logging(log_dir: str = None, level: str = 'INFO') -> None:
        if Logger._test_mode:
            log_dir = Logger._test_log_dir
        elif not log_dir:
            log_dir = os.path.join(os.getcwd(), 'logs')

        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'radio.log')

        # Remove existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Set level
        root_logger.setLevel(getattr(logging, level.upper()))

        # Add handlers
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        root_logger.addHandler(file_handler)

    def debug(self, msg: str) -> None:
        self.logger.debug(msg)

    def info(self, msg: str) -> None:
        self.logger.info(msg)

    def warning(self, msg: str) -> None:
        self.logger.warning(msg)

    def error(self, msg: str) -> None:
        self.logger.error(msg)

    def critical(self, msg: str) -> None:
        self.logger.critical(msg)

    @staticmethod
    def set_level(level: str) -> None:
        """Change log level dynamically"""
        logging.getLogger().setLevel(getattr(logging, level.upper()))