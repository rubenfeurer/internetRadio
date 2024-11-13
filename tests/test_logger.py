import unittest
import os
import shutil
from pathlib import Path
from src.utils.logger import Logger
import tempfile

class TestLogger(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.test_log_dir = tempfile.mkdtemp()
        self.app_log_path = os.path.join(self.test_log_dir, 'app.log')
        
        # Reset and initialize logger
        Logger.reset()
        Logger.setup_logging(app_log_path=self.app_log_path)
        
        # Get logger instance
        self.logger = Logger.get_logger('test')

    def tearDown(self):
        """Clean up test environment"""
        Logger.reset()
        if os.path.exists(self.test_log_dir):
            for file in os.listdir(self.test_log_dir):
                os.remove(os.path.join(self.test_log_dir, file))
            os.rmdir(self.test_log_dir)

    def test_logger_instance(self):
        """Test logger singleton pattern"""
        logger1 = Logger("test1")
        logger2 = Logger("test2")
        self.assertEqual(id(logger1), id(logger2))

    def test_log_files_created(self):
        """Test log file creation"""
        self.assertTrue(os.path.exists(self.test_log_dir))
        self.logger.info("Test message")
        self.assertTrue(os.path.exists(self.app_log_path))

    def test_logging_works(self):
        """Test different log levels"""
        test_messages = {
            "debug": "Debug message",
            "info": "Info message",
            "warning": "Warning message",
            "error": "Error message",
            "critical": "Critical message"
        }

        # Write messages
        self.logger.debug(test_messages["debug"])
        self.logger.info(test_messages["info"])
        self.logger.warning(test_messages["warning"])
        self.logger.error(test_messages["error"])
        self.logger.critical(test_messages["critical"])

        # Read log file
        with open(self.app_log_path, 'r') as f:
            log_content = f.read()

        # Check messages (except debug, which is filtered by default INFO level)
        for level, msg in test_messages.items():
            if level != "debug":
                self.assertIn(msg, log_content)

    def test_log_level_change(self):
        """Test dynamic log level change"""
        # Set to DEBUG
        Logger.set_level("DEBUG")
        self.logger.debug("Debug test")

        with open(self.app_log_path, 'r') as f:
            log_content = f.read()
            self.assertIn("Debug test", log_content)

        # Set back to INFO
        Logger.set_level("INFO")

if __name__ == '__main__':
    unittest.main() 