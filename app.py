from flask import Flask, render_template, jsonify, request
from player import RadioPlayer
from stream_manager import StreamManager
import tomli

app = Flask(__name__)
player = RadioPlayer()
stream_manager = StreamManager()

# Load default stations from config
def load_default_stations():
    try:
        with open('config.toml', 'rb') as f:
            config = tomli.load(f)
            default_stations = []
            for station_name in config['default_stations']:
                station = stream_manager.get_stream_by_name(station_name)
                if station:
                    default_stations.append(station)
            return default_stations
    except Exception as e:
        print(f"Error loading config: {e}")
        return []

# Initialize with default stations
selected_stations = load_default_stations()

@app.route('/')
def index():
    return render_template('index.html', stations=selected_stations)

@app.route('/stations/<int:slot_index>')
def stations(slot_index):
    if 0 <= slot_index < 3:  # Validate slot index
        all_streams = stream_manager.get_all_streams()
        return render_template('stations.html', 
                             streams=all_streams, 
                             slot_index=slot_index)
    return "Invalid slot", 400

@app.route('/api/select_station', methods=['POST'])
def select_station():
    data = request.get_json()
    station_name = data.get('name')
    slot_index = data.get('slot')
    
    if station_name and 0 <= slot_index < 3:
        station = stream_manager.get_stream_by_name(station_name)
        if station:
            # Update the station in the specified slot
            selected_stations[slot_index] = station
            return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/play', methods=['POST'])
def play_stream():
    data = request.get_json()
    url = data.get('url')
    if url:
        success = player.play(url)
        return jsonify({'success': success})
    return jsonify({'success': False})

@app.route('/api/stop', methods=['POST'])
def stop_stream():
    success = player.stop()
    return jsonify({'success': success})

@app.route('/api/status')
def get_status():
    return jsonify({
        'playing': player.is_playing(),
        'current_stream': player.get_current_stream()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)