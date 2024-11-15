import unittest
from unittest.mock import patch, MagicMock
import logging
import os
from src.utils.logger import Logger, AlsaFilter

class TestLogger(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Clear existing loggers and instances
        logging.getLogger().handlers = []
        logging.Logger.manager.loggerDict.clear()
        if hasattr(Logger, '_instances'):
            Logger._instances = {}
        
        # Create test directory
        self.test_log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(self.test_log_dir, exist_ok=True)
        
        # Create patches
        self.rotating_patcher = patch('src.utils.logger.RotatingFileHandler')
        self.stream_patcher = patch('src.utils.logger.logging.StreamHandler', 
                                  return_value=logging.NullHandler())
        
        # Start patches
        self.mock_rotating = self.rotating_patcher.start()
        self.mock_stream = self.stream_patcher.start()
        
        # Configure mock rotating handler
        self.mock_rotating_instance = MagicMock()
        self.mock_rotating.return_value = self.mock_rotating_instance

    def tearDown(self):
        """Clean up after tests"""
        # Stop patches
        self.rotating_patcher.stop()
        self.stream_patcher.stop()
        
        # Clear loggers
        logging.getLogger().handlers = []
        logging.Logger.manager.loggerDict.clear()
        if hasattr(Logger, '_instances'):
            Logger._instances = {}
        
        # Clean up test directory
        for filename in os.listdir(self.test_log_dir):
            file_path = os.path.join(self.test_log_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception:
                pass

    def test_log_size_limits(self):
        """Test that log size limits are properly configured"""
        logger = Logger('test')
        
        # Verify RotatingFileHandler was created with correct parameters
        self.mock_rotating.assert_called_once()
        
        # Get the call arguments
        args, kwargs = self.mock_rotating.call_args
        
        # Verify size limits
        self.assertEqual(kwargs.get('maxBytes'), 1024 * 1024)  # 1MB
        self.assertEqual(kwargs.get('backupCount'), 2)  # 2 backup files
        self.assertEqual(kwargs.get('encoding'), 'utf-8')

    def test_message_length_limit(self):
        """Test that log messages are truncated"""
        logger = Logger('test')
        
        # Get formatter from mock handler
        formatter_call = self.mock_rotating_instance.setFormatter.call_args
        formatter = formatter_call[0][0]
        
        # Create a test record with a long message
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='x' * 300,  # Message longer than 200 chars
            args=(),
            exc_info=None
        )
        
        # Format the record
        formatted = formatter.format(record)
        
        # Verify message was truncated (including timestamp, level, etc.)
        self.assertLess(len(formatted), 250)  # Allow for timestamp and level

    def test_development_mode(self):
        """Test console handler only added in development mode"""
        # Test without DEVELOPMENT env var
        if 'DEVELOPMENT' in os.environ:
            del os.environ['DEVELOPMENT']
        
        logger1 = Logger('test')
        self.mock_stream.assert_not_called()
        
        # Test with DEVELOPMENT env var
        with patch.dict('os.environ', {'DEVELOPMENT': 'true'}):
            self.mock_stream.reset_mock()
            logger2 = Logger('test2')
            self.mock_stream.assert_called_once()

    def test_log_level_filtering(self):
        """Test that only INFO and above are logged"""
        logger = Logger('test')
        
        # Verify file handler level
        self.mock_rotating_instance.setLevel.assert_called_with(logging.INFO)
        
        # Verify logger level
        self.assertEqual(logger.logger.level, logging.INFO)

    def test_singleton_behavior(self):
        """Test that multiple instances with same name reuse the logger"""
        # Create first logger
        logger1 = Logger('test')
        first_logger = logger1.logger
        
        # Reset mock to ensure clean state
        self.mock_rotating.reset_mock()
        
        # Create second logger with same name
        logger2 = Logger('test')
        second_logger = logger2.logger
        
        # Verify it's the same logger instance
        self.assertIs(first_logger, second_logger)
        
        # Verify RotatingFileHandler was not called again
        self.mock_rotating.assert_not_called()

    def test_log_file_creation(self):
        """Test that log files are created with correct names"""
        test_cases = [
            ('app', 'app.log'),
            ('network', 'wifi.log'),
            ('radio', 'radio.log')
        ]
        
        for logger_name, expected_file in test_cases:
            with self.subTest(logger_name=logger_name):
                # Reset mocks for each test case
                self.mock_rotating.reset_mock()
                
                logger = Logger(logger_name)
                self.mock_rotating.assert_called_once()
                args, _ = self.mock_rotating.call_args
                self.assertTrue(args[0].endswith(expected_file))
    