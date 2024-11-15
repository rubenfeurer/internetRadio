import unittest
from unittest.mock import patch, MagicMock
from src.utils.logger import Logger
from logging.handlers import RotatingFileHandler
import logging
import os
import tempfile
import shutil

class TestLogger(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test logs
        self.test_dir = tempfile.mkdtemp()
        # Reset singleton instances
        Logger._instances = {}
        # Reset logging handlers
        logging.getLogger().handlers = []
        
    def test_logger_initialization(self):
        """Test that logger is properly initialized with temporary directory"""
        logger = Logger('test', log_dir=self.test_dir)
        self.assertIsNotNone(logger)
        self.assertTrue(hasattr(logger, 'info'))
        self.assertTrue(hasattr(logger, 'error'))
        self.assertTrue(os.path.exists(self.test_dir))
        
    @patch('src.utils.logger.RotatingFileHandler')
    def test_logger_singleton(self, mock_handler):
        """Test that logger follows singleton pattern"""
        # Configure mock handler properly
        mock_handler.return_value.level = logging.INFO
        
        logger1 = Logger('test', log_dir=self.test_dir)
        logger2 = Logger('test', log_dir=self.test_dir)
        
        self.assertEqual(id(logger1), id(logger2))
        mock_handler.assert_called_once()

    def test_logging_works(self):
        """Test that logging actually writes to files"""
        test_message = "Test log message"
        logger = Logger('test', log_dir=self.test_dir)
        
        # Log the message directly using the logger's existing handlers
        logger.info(test_message)
        
        # Verify the log file
        log_file = os.path.join(self.test_dir, 'test.log')
        self.assertTrue(os.path.exists(log_file))
        with open(log_file, 'r') as f:
            content = f.read()
            self.assertIn(test_message, content)

    def test_fallback_to_console_logger(self):
        """Test that logger falls back to console logging when file access fails"""
        with patch('os.makedirs', side_effect=PermissionError):
            logger = Logger('test', log_dir='/nonexistent/dir')
            
            # Verify it's a standard logging.Logger
            self.assertIsInstance(logger, logging.Logger)
            
            # Verify it has a console handler
            has_console_handler = any(
                isinstance(handler, logging.StreamHandler) 
                for handler in logger.handlers
            )
            self.assertTrue(has_console_handler)
            
            # Verify it can log without errors
            try:
                logger.info("Test message")
                logger.error("Test error")
            except Exception as e:
                self.fail(f"Logging failed with fallback logger: {e}")

    def test_fallback_logger_singleton(self):
        """Test that fallback logger also maintains singleton pattern"""
        with patch('os.makedirs', side_effect=PermissionError):
            logger1 = Logger('test', log_dir='/nonexistent/dir')
            logger2 = Logger('test', log_dir='/nonexistent/dir')
            
            self.assertEqual(id(logger1), id(logger2))

    def tearDown(self):
        # Clean up logger instances
        Logger._instances = {}
        
        # Clean up temporary directory
        try:
            shutil.rmtree(self.test_dir)
        except (PermissionError, OSError):
            pass  # Handle file lock issues

if __name__ == '__main__':
    unittest.main() 