import unittest
import logging
import os
from src.utils.logger import Logger

class TestLogger(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.app_log_path = 'logs/test.log'
        self.network_log_path = 'logs/network_debug.log'
        
        # Clean up any existing log files
        for path in [self.app_log_path, self.network_log_path]:
            if os.path.exists(path):
                os.remove(path)
    
    def test_logger_instance(self):
        """Test that Logger creates singleton instances"""
        # Setup logging first
        Logger.setup_logging(
            app_log_path=self.app_log_path,
            network_log_path=self.network_log_path
        )
        
        # Get two instances with the same name
        logger1 = Logger('test_module')
        logger2 = Logger('test_module')
        
        # They should be the same object
        self.assertIs(logger1, logger2)
    
    def test_logging_works(self):
        """Test that logging actually writes to files"""
        Logger.setup_logging(
            app_log_path=self.app_log_path,
            network_log_path=self.network_log_path
        )
        logger = Logger('test_module')
        test_message = "Test log message"
        logger.info(test_message)
        
        with open(self.app_log_path, 'r') as f:
            log_content = f.read()
        self.assertIn(test_message, log_content)
    
    def test_log_files_created(self):
        """Test that log files are created"""
        Logger.setup_logging(
            app_log_path=self.app_log_path,
            network_log_path=self.network_log_path
        )
        self.assertTrue(os.path.exists(self.app_log_path))
        self.assertTrue(os.path.exists(self.network_log_path))
    
    def test_log_level_change(self):
        """Test changing log levels"""
        Logger.setup_logging(
            app_log_path=self.app_log_path,
            network_log_path=self.network_log_path
        )
        logger = Logger('test_module')
        logger.setLevel(logging.DEBUG)
        self.assertEqual(logger.getEffectiveLevel(), logging.DEBUG)

    def tearDown(self):
        """Clean up after tests"""
        for path in [self.app_log_path, self.network_log_path]:
            if os.path.exists(path):
                os.remove(path) 