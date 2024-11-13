import unittest
from unittest.mock import patch, MagicMock
import json
import logging
from flask import Flask
import pytest

class TestWebController(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Configure logging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        # Create mocks for dependencies
        self.mock_radio = MagicMock()
        self.mock_network = MagicMock()
        
        # Configure default returns
        self.mock_radio.get_default_streams.return_value = [
            {'name': 'Test Stream 1', 'url': 'http://test1.com'},
            {'name': 'Test Stream 2', 'url': 'http://test2.com'},
            {'name': 'Test Stream 3', 'url': 'http://test3.com'}
        ]
        
        self.mock_network.get_connection_status.return_value = {
            'is_connected': True,
            'ssid': 'Test Network',
            'ip_address': '192.168.1.100'
        }
        
        # Import and create WebController
        from src.web.web_controller import WebController
        with patch('src.web.web_controller.Logger'):
            self.web = WebController(self.mock_radio, self.mock_network)
            
        # Configure Flask for testing
        self.web.app.config['TESTING'] = True
        self.client = self.web.app.test_client()
        
        # Configure mock responses
        self.mock_response = {
            'status': 'success',
            'success': True,
            'data': {'test': 'data'}
        }
        
    def test_index_route(self):
        """Test index page route"""
        with self.web.app.test_request_context('/'):
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
            self.mock_radio.get_default_streams.assert_called_once()
            self.mock_network.get_connection_status.assert_called_once()
        
    def test_stream_select_route(self):
        """Test stream selection page"""
        self.mock_radio.get_spare_links.return_value = [
            {'name': 'Spare 1', 'url': 'http://spare1.com'},
            {'name': 'Spare 2', 'url': 'http://spare2.com'}
        ]
        
        with self.web.app.test_request_context('/stream-select/link1'):
            response = self.client.get('/stream-select/link1')
            self.assertEqual(response.status_code, 200)
            self.mock_radio.get_spare_links.assert_called_once()
        
    def test_wifi_scan_route(self):
        """Test WiFi scanning endpoint"""
        self.mock_network.scan_networks.return_value = ['Network1', 'Network2']
        self.mock_network.get_current_network.return_value = 'Network1'
        self.mock_network.get_saved_networks.return_value = ['Network1']
        
        with self.web.app.test_request_context('/wifi-scan'):
            response = self.client.get('/wifi-scan')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(data['status'], 'complete')
            self.assertEqual(len(data['networks']), 2)
            self.assertEqual(data['current_network'], 'Network1')
        
    def test_connect_wifi_route(self):
        """Test WiFi connection endpoint"""
        self.mock_network.connect_wifi.return_value = True
        
        with self.web.app.test_request_context('/connect', method='POST', 
            data={'ssid': 'TestNetwork', 'password': 'TestPassword'}):
            response = self.client.post('/connect', data={
                'ssid': 'TestNetwork',
                'password': 'TestPassword'
            })
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(data['status'], 'success')
        
    def test_forget_network_route(self):
        """Test network forgetting endpoint"""
        self.mock_network.forget_network.return_value = True
        
        with self.web.app.test_request_context('/forget_network', method='POST',
            json={'ssid': 'TestNetwork'}):
            response = self.client.post('/forget_network', 
                                      json={'ssid': 'TestNetwork'},
                                      content_type='application/json')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(data['status'], 'success')
        
    def test_play_stream_route(self):
        """Test stream playback endpoint"""
        self.mock_radio.start_playback.return_value = True
        
        with self.web.app.test_request_context('/play-stream', method='POST',
            data={'url': 'http://test.com/stream'}):
            response = self.client.post('/play-stream', data={
                'url': 'http://test.com/stream'
            })
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertTrue(data['success'])
        
    def test_stop_stream_route(self):
        """Test stream stopping endpoint"""
        with self.web.app.test_request_context('/stop-stream', method='POST'):
            response = self.client.post('/stop-stream')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertTrue(data['success'])
        
    def test_stream_status_route(self):
        """Test stream status endpoint"""
        self.mock_radio.get_playback_status.return_value = {
            'is_running': True,
            'current_stream': 'link1'
        }
        
        with self.web.app.test_request_context('/stream-status'):
            response = self.client.get('/stream-status')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertTrue(data['is_running'])
            self.assertEqual(data['current_stream'], 'link1')
        
    def test_error_handling(self):
        """Test error handling in routes"""
        # Test missing parameters
        with self.web.app.test_request_context('/connect', method='POST'):
            response = self.client.post('/connect', data={})
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(data['status'], 'error')

    def test_404_error_handler(self):
        """Test 404 error handler"""
        with self.web.app.test_request_context('/nonexistent-page'):
            response = self.client.get('/nonexistent-page')
            self.assertEqual(response.status_code, 404)
            self.assertIn(b'Error 404', response.data)
            self.assertIn(b'Page not found', response.data)

    def test_500_error_handler(self):
        """Test 500 error handler"""
        # Mock radio controller to raise an exception
        self.mock_radio.get_default_streams.side_effect = Exception("Test error")
        
        with self.web.app.test_request_context('/'):
            response = self.client.get('/')
            self.assertEqual(response.status_code, 500)
            self.assertIn(b'Error 500', response.data)
            self.assertIn(b'Internal server error', response.data)

    def test_network_status_route(self):
        """Test network status endpoint"""
        test_status = {
            'is_connected': True,
            'ssid': 'TestNetwork',
            'ip_address': '192.168.1.100',
            'signal_strength': -65
        }
        self.mock_network.get_connection_status.return_value = test_status
        
        with self.web.app.test_request_context('/network-status'):
            response = self.client.get('/network-status')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(data, test_status)

    def test_network_status_error(self):
        """Test network status endpoint error handling"""
        self.mock_network.get_connection_status.side_effect = Exception("Network error")
        
        with self.web.app.test_request_context('/network-status'):
            response = self.client.get('/network-status')
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.get_data(as_text=True))
            self.assertIn('error', data)

    def test_update_stream_validation(self):
        """Test update stream endpoint parameter validation"""
        test_cases = [
            ({}, 'Channel and URL required'),
            ({'channel': 'link1'}, 'Channel and URL required'),
            ({'selected_link': 'http://test.com'}, 'Channel and URL required')
        ]
        
        for test_data, expected_error in test_cases:
            with self.web.app.test_request_context('/update-stream', method='POST',
                data=test_data):
                response = self.client.post('/update-stream', data=test_data)
                self.assertEqual(response.status_code, 400)
                data = json.loads(response.get_data(as_text=True))
                self.assertFalse(data['success'])
                self.assertEqual(data['error'], expected_error)

    def test_update_stream_success(self):
        """Test successful stream update"""
        self.mock_radio.update_stream.return_value = True
        test_data = {
            'channel': 'link1',
            'selected_link': 'http://test.com/stream'
        }
        
        with self.web.app.test_request_context('/update-stream', method='POST',
            data=test_data):
            response = self.client.post('/update-stream', data=test_data)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertTrue(data['success'])
            self.mock_radio.update_stream.assert_called_once_with(
                'link1', 'http://test.com/stream'
            )

    def test_update_stream_failure(self):
        """Test failed stream update"""
        self.mock_radio.update_stream.return_value = False
        test_data = {
            'channel': 'link1',
            'selected_link': 'http://test.com/stream'
        }
        
        with self.web.app.test_request_context('/update-stream', method='POST',
            data=test_data):
            response = self.client.post('/update-stream', data=test_data)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertFalse(data['success'])

    def test_stop_method(self):
        """Test web controller stop method"""
        with self.web.app.test_request_context('/'):
            mock_environ = {'werkzeug.server.shutdown': MagicMock()}
            with patch('flask.request.environ', new=mock_environ):
                self.web.stop()
                mock_environ['werkzeug.server.shutdown'].assert_called_once()

    def test_stop_method_error(self):
        """Test web controller stop method when not running with Werkzeug"""
        with self.web.app.test_request_context('/'):
            with patch('flask.request.environ', new={}):
                with self.assertRaises(RuntimeError) as context:
                    self.web.stop()
                self.assertEqual(
                    str(context.exception),
                    'Not running with the Werkzeug Server'
                )

if __name__ == '__main__':
    unittest.main() 