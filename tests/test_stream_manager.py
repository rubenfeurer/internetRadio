import unittest
import tempfile
import os
import toml
from pathlib import Path
from src.utils.stream_manager import StreamManager, RadioStream
from src.utils.logger import Logger
import shutil

class TestStreamManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test config
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        self.log_dir = os.path.join(self.temp_dir, 'logs')
        
        # Set logger to test mode
        Logger.reset()
        Logger.set_test_mode(self.log_dir)
        
        # Create test streams file
        self.test_streams = {
            'links': [
                {
                    'name': 'Test Radio 1',
                    'url': 'http://test1.com/stream',
                    'country': 'Test Country',
                    'location': 'Test City'
                },
                {
                    'name': 'Test Radio 2',
                    'url': 'http://test2.com/stream',
                    'country': 'Test Country',
                    'location': 'Another City'
                }
            ]
        }
        
        with open(self.config_dir / 'streams.toml', 'w') as f:
            toml.dump(self.test_streams, f)
            
        self.stream_manager = StreamManager(config_dir=self.temp_dir)
        
    def tearDown(self):
        """Clean up test files and directories"""
        try:
            shutil.rmtree(self.temp_dir)  # Use shutil.rmtree instead of manual deletion
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            Logger.reset()  # Reset logger state
        
    def test_load_streams(self):
        """Test loading streams from file"""
        streams = self.stream_manager.get_all_streams()
        self.assertEqual(len(streams), 2)
        self.assertEqual(streams[0].name, 'Test Radio 1')
        self.assertEqual(streams[1].url, 'http://test2.com/stream')
        
    def test_get_stream_by_name(self):
        """Test getting stream by name"""
        stream = self.stream_manager.get_stream_by_name('Test Radio 1')
        self.assertIsNotNone(stream)
        self.assertEqual(stream.url, 'http://test1.com/stream')
        
        # Test non-existent stream
        stream = self.stream_manager.get_stream_by_name('Non Existent')
        self.assertIsNone(stream)
        
    def test_get_streams_by_country(self):
        """Test getting streams by country"""
        streams = self.stream_manager.get_streams_by_country('Test Country')
        self.assertEqual(len(streams), 2)
        
    def test_get_streams_by_location(self):
        """Test getting streams by location"""
        streams = self.stream_manager.get_streams_by_location('Test City')
        self.assertEqual(len(streams), 1)
        self.assertEqual(streams[0].name, 'Test Radio 1')
        
    def test_add_stream(self):
        """Test adding new stream"""
        new_stream = RadioStream(
            name='Test Radio 3',
            url='http://test3.com/stream',
            country='Test Country',
            location='New City'
        )
        
        # Add new stream
        self.assertTrue(self.stream_manager.add_stream(new_stream))
        
        # Verify stream was added
        streams = self.stream_manager.get_all_streams()
        self.assertEqual(len(streams), 3)
        
        # Try to add duplicate stream
        self.assertFalse(self.stream_manager.add_stream(new_stream))
        
    def test_remove_stream(self):
        """Test removing stream"""
        # Remove existing stream
        self.assertTrue(self.stream_manager.remove_stream('Test Radio 1'))
        
        # Verify stream was removed
        streams = self.stream_manager.get_all_streams()
        self.assertEqual(len(streams), 1)
        
        # Try to remove non-existent stream
        self.assertFalse(self.stream_manager.remove_stream('Non Existent'))

    def test_save_streams(self):
        """Test saving streams to file"""
        new_stream = RadioStream(
            name='Test Radio 3',
            url='http://test3.com/stream',
            country='Test Country',
            location='New City'
        )
        
        self.assertTrue(self.stream_manager.add_stream(new_stream))
        
        # Verify stream was added
        streams = self.stream_manager.get_all_streams()
        self.assertEqual(len(streams), 3)
        
        # Save streams to file
        self.assertTrue(self.stream_manager.save_streams())
        
        # Load streams from file
        self.stream_manager.load_streams()
        
        # Verify streams were loaded correctly
        streams = self.stream_manager.get_all_streams()
        self.assertEqual(len(streams), 3)
        self.assertEqual(streams[0].name, 'Test Radio 1')
        self.assertEqual(streams[1].url, 'http://test2.com/stream')
        self.assertEqual(streams[2].name, 'Test Radio 3')