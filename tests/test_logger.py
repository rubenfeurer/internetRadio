import unittest
import os
import logging
import tempfile
import time
from src.utils.logger import setup_logging, log_system_status

class TestLogger(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = self.temp_dir
        
    def tearDown(self):
        # Clean up temporary files after tests
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    def test_log_files_created(self):
        logger, network_logger = setup_logging(log_dir=self.log_dir)
        
        # Check if log files exist
        self.assertTrue(os.path.exists(os.path.join(self.log_dir, 'app.log')))
        self.assertTrue(os.path.exists(os.path.join(self.log_dir, 'network_debug.log')))
    
    def test_logging_works(self):
        logger, network_logger = setup_logging(log_dir=self.log_dir)
        test_message = "Test log message"
        network_logger.info(test_message)
        
        # Give a small delay for file writing
        time.sleep(0.1)
        
        with open(os.path.join(self.log_dir, 'network_debug.log'), 'r') as f:
            log_content = f.read()
            self.assertIn(test_message, log_content)
    
    def test_system_status_logging(self):
        logger, _ = setup_logging(log_dir=self.log_dir)
        success = log_system_status(log_dir=self.log_dir)
        
        # Give a small delay for file writing
        time.sleep(0.1)
        
        # First check if the function succeeded
        self.assertTrue(success, "System status logging failed")
        
        # Then check if system status was logged
        with open(os.path.join(self.log_dir, 'app.log'), 'r') as f:
            log_content = f.read()
            self.assertTrue(
                any(status in log_content for status in 
                    ["Memory Status:", "Disk Space:", "Python Processes:"]),
                f"System status not found in log content: {log_content}"
            )

if __name__ == '__main__':
    unittest.main() 