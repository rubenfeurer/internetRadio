import unittest
from unittest.mock import patch, Mock, MagicMock
import signal
import sys
from pathlib import Path

class TestMain(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Clear module cache first
        if 'main' in sys.modules:
            del sys.modules['main']
            
        # Create mocks
        self.network_mock = Mock()
        self.network_mock.initialize.return_value = False
        self.network_mock.cleanup = Mock()
        
        self.radio_controller_mock = Mock()
        self.radio_controller_mock.initialize.return_value = True
        
        self.radio_instance = Mock()
        self.radio_instance.network_controller = self.network_mock
        self.radio_instance.radio_controller = self.radio_controller_mock
        
        # Set up patches
        self.patches = [
            patch('main.logger', new_callable=Mock),
            patch('main.InternetRadio', return_value=self.radio_instance),
            patch('builtins.print'),  # Suppress print statements
            patch('main.time.sleep'),  # Don't actually sleep
            patch('main.signal.signal')  # Don't register signal handlers
        ]
        
        # Start all patches
        for p in self.patches:
            p.start()
            
        self.addCleanup(patch.stopall)
    
    def test_network_initialization_failure(self):
        """Test network initialization failure scenario"""
        # Import main after patches are in place
        import main
        
        # Run main with network initialization configured to fail
        self.network_mock.initialize.return_value = False
        
        # Execute main
        result = main.main()
        
        # Verify:
        # 1. Network initialization was attempted
        self.network_mock.initialize.assert_called_once()
        
        # 2. Cleanup was called
        self.network_mock.cleanup.assert_called_once()
        
        # 3. Error was logged
        main.logger.error.assert_any_call("Failed to initialize network controller")
        
        # 4. Function returned error code
        self.assertEqual(result, 1)
        
        # 5. Main loop was not entered (sleep not called)
        main.time.sleep.assert_not_called()

if __name__ == '__main__':
    unittest.main() 