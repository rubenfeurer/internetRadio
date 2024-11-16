import json
import os

class StateManager:
    def __init__(self, state_file='config/radio_state.json'):
        self.state_file = state_file
        self.default_state = {
            'selected_stations': [],
            'current_stream': None
        }
        self.load_state()
    
    def load_state(self):
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    self.state = json.load(f)
            else:
                self.state = self.default_state.copy()
        except Exception as e:
            print(f"Error loading state: {e}")
            self.state = self.default_state.copy()
    
    def save_state(self):
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f)
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def get_selected_stations(self):
        return self.state.get('selected_stations', [])
    
    def set_selected_stations(self, stations):
        self.state['selected_stations'] = stations
        self.save_state()
    
    def get_current_stream(self):
        return self.state.get('current_stream')
    
    def set_current_stream(self, stream):
        self.state['current_stream'] = stream
        self.save_state() 