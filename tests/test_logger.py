import unittest
from unittest.mock import patch, MagicMock
from src.utils.logger import Logger
import logging
import os
import tempfile
import shutil

class TestLogger(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test logs
        self.test_dir = tempfile.mkdtemp()
        # Clean up any existing logger state
        Logger.cleanup()
        
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
        mock_instance = MagicMock()
        mock_handler.return_value = mock_instance
        
        logger1 = Logger('test', log_dir=self.test_dir)
        logger2 = Logger('test', log_dir=self.test_dir)
        
        self.assertEqual(id(logger1), id(logger2))
        mock_handler.assert_called_once()

    def test_logging_works(self):
        """Test that logging actually writes to files"""
        test_message = "Test log message"
        logger = Logger('test', log_dir=self.test_dir)
        logger.info(test_message)
        
        log_file = os.path.join(self.test_dir, 'test.log')
        self.assertTrue(os.path.exists(log_file))
        with open(log_file, 'r') as f:
            content = f.read()
            self.assertIn(test_message, content)

    def tearDown(self):
        # Clean up logger resources first
        Logger.cleanup()
        
        # Clean up temporary directory
        try:
            shutil.rmtree(self.test_dir)
        except (PermissionError, OSError):
            pass  # Handle file lock issues 