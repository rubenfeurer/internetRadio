import unittest
import os
import shutil
from pathlib import Path
from src.utils.logger import Logger
import tempfile

class TestLogger(unittest.TestCase):
    def setUp(self):
        self.test_log_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_log_dir, "radio.log")
        
        # Clean start
        if os.path.exists(self.test_log_dir):
            shutil.rmtree(self.test_log_dir)
        os.makedirs(self.test_log_dir)
        
        # Set logger to test mode
        Logger.reset()
        Logger.set_test_mode(self.test_log_dir)
        self.logger = Logger("test")

    def tearDown(self):
        try:
            shutil.rmtree(self.test_log_dir)
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            Logger.reset()

    def test_logger_instance(self):
        """Test logger singleton pattern"""
        logger1 = Logger("test1")
        logger2 = Logger("test2")
        self.assertEqual(id(logger1), id(logger2))

    def test_log_files_created(self):
        """Test log file creation"""
        self.assertTrue(os.path.exists(self.test_log_dir))
        self.logger.info("Test message")
        self.assertTrue(os.path.exists(self.log_file))

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
        with open(self.log_file, 'r') as f:
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

        with open(self.log_file, 'r') as f:
            log_content = f.read()
            self.assertIn("Debug test", log_content)

        # Set back to INFO
        Logger.set_level("INFO")

if __name__ == '__main__':
    unittest.main() 