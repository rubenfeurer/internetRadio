import logging
from typing import Optional

class Logger:
    """Custom logger wrapper"""
    def __init__(self, name: str, level: Optional[int] = None):
        self.logger = logging.getLogger(name)
        if level:
            self.logger.setLevel(level)
    
    def info(self, message: str, *args) -> None:
        self.logger.info(message, *args)
    
    def error(self, message: str, *args) -> None:
        self.logger.error(message, *args)
    
    def debug(self, message: str, *args) -> None:
        self.logger.debug(message, *args)
    
    def warning(self, message: str, *args) -> None:
        self.logger.warning(message, *args)