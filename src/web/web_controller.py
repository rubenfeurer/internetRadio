from flask import Flask, render_template, request, jsonify, Response
import threading
from typing import Dict, List, Optional
import json
from ..controllers.network_controller import NetworkController
from ..controllers.radio_controller import RadioController
from ..utils.logger import Logger
from threading import Thread

class WebController:
    def __init__(self, radio_controller=None, network_controller=None):
        self.logger = Logger.get_logger(__name__)
        self.radio = radio_controller
        self.network = network_controller
        self.app = Flask(__name__)
        self.thread = None  # Initialize thread attribute
        self._setup_routes()
        
        # Add error handlers
        self.setup_error_handlers()

    def setup_error_handlers(self) -> None:
        """Set up Flask error handlers"""
        
        @self.app.errorhandler(404)
        def not_found_error(error):
            return render_template('error.html', 
                                error_code=404, 
                                message="Page not found"), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            return render_template('error.html', 
                                error_code=500, 
                                message="Internal server error"), 500

        @self.app.errorhandler(Exception)
        def handle_exception(error):
            return render_template('error.html',
                                error_code=500,
                                message="Internal server error"), 500

    def _setup_routes(self) -> None:
        """Set up all Flask routes"""
        
        @self.app.route('/')
        def index():
            try:
                default_streams = self.radio.get_default_streams()
                network_status = self.network.get_connection_status()
                return render_template('index.html', 
                                    default_streams=default_streams,
                                    network_status=network_status)
            except Exception as e:
                self.logger.error(f"Error rendering index: {e}")
                return render_template('error.html',
                                    error_code=500,
                                    message="Internal server error"), 500

        @self.app.route('/stream-select/<channel>')
        def stream_select(channel):
            try:
                spare_links = self.radio.get_spare_links()
                return render_template('stream_select.html', 
                                    channel=channel,
                                    spare_links=spare_links)
            except Exception as e:
                self.logger.error(f"Error rendering stream select: {e}")
                return "Error loading page", 500

        @self.app.route('/wifi-settings')
        def wifi_settings():
            try:
                return render_template('wifi_settings.html')
            except Exception as e:
                self.logger.error(f"Error rendering WiFi settings: {e}")
                return "Error loading page", 500

        @self.app.route('/wifi-scan')
        def wifi_scan():
            try:
                networks = self.network.scan_networks()
                current = self.network.get_current_network()
                saved = self.network.get_saved_networks()
                return jsonify({
                    'status': 'complete',
                    'networks': networks,
                    'current_network': current,
                    'saved_networks': saved
                })
            except Exception as e:
                self.logger.error(f"Error scanning networks: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/connect', methods=['POST'])
        def connect_wifi():
            try:
                ssid = request.form.get('ssid')
                password = request.form.get('password')
                if not ssid:
                    return jsonify({'status': 'error', 'message': 'SSID required'}), 400
                
                success = self.network.connect_wifi(ssid, password)
                return jsonify({'status': 'success' if success else 'error'})
            except Exception as e:
                self.logger.error(f"Error connecting to WiFi: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/forget_network', methods=['POST'])
        def forget_network():
            try:
                data = request.get_json()
                ssid = data.get('ssid')
                if not ssid:
                    return jsonify({'status': 'error', 'message': 'SSID required'}), 400
                
                success = self.network.forget_network(ssid)
                return jsonify({'status': 'success' if success else 'error'})
            except Exception as e:
                self.logger.error(f"Error forgetting network: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/play-stream', methods=['POST'])
        def play_stream():
            try:
                url = request.form.get('url')
                if not url:
                    return jsonify({'success': False, 'error': 'URL required'}), 400
                
                success = self.radio.start_playback(url)
                return jsonify({'success': success})
            except Exception as e:
                self.logger.error(f"Error playing stream: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/stop-stream', methods=['POST'])
        def stop_stream():
            try:
                self.radio.stop_playback()
                return jsonify({'success': True})
            except Exception as e:
                self.logger.error(f"Error stopping stream: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/stream-status')
        def stream_status():
            """Get current stream playback status"""
            try:
                status = self.radio.get_playback_status()
                return jsonify(status)
            except Exception as e:
                self.logger.error(f"Error getting stream status: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/update-stream', methods=['POST'])
        def update_stream():
            """Update stream configuration"""
            try:
                channel = request.form.get('channel')
                url = request.form.get('selected_link')
                if not channel or not url:
                    return jsonify({
                        'success': False, 
                        'error': 'Channel and URL required'
                    }), 400
                
                success = self.radio.update_stream(channel, url)
                return jsonify({'success': success})
            except Exception as e:
                self.logger.error(f"Error updating stream: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/network-status')
        def network_status():
            """Get current network status"""
            try:
                status = self.network.get_connection_status()
                return jsonify(status)
            except Exception as e:
                self.logger.error(f"Error getting network status: {e}")
                return jsonify({'error': str(e)}), 500

    def start(self) -> None:
        """Start the Flask application in a separate thread"""
        logger = Logger.get_logger(__name__)
        logger.debug("Starting web interface")
        if not self.thread or not self.thread.is_alive():
            self.thread = Thread(target=self._run)
            self.thread.daemon = True
            self.thread.start()
            logger.info("Web interface started")

    def stop(self) -> None:
        """Stop the Flask application"""
        self.logger.info("Stopping web interface")
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()