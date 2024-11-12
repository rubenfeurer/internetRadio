from flask import Flask, render_template, request, jsonify, Response
import threading
from typing import Dict, List, Optional
import json
from ..controllers.network_controller import NetworkController
from ..controllers.radio_controller import RadioController
from ..utils.logger import Logger

class WebController:
    def __init__(self, radio_controller: RadioController, network_controller: NetworkController):
        self.logger = Logger(__name__)
        self.app = Flask(__name__, 
                        template_folder='../../templates',
                        static_folder='../../static')
        self.radio = radio_controller
        self.network = network_controller
        self.setup_routes()

    def setup_routes(self) -> None:
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
                return "Error loading page", 500

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

    def run(self, host: str = '0.0.0.0', port: int = 5000) -> None:
        """Run the Flask application"""
        self.app.run(host=host, port=port, debug=False, threaded=True) 