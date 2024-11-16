import tomli

class StreamManager:
    def __init__(self, toml_file='streams.toml'):
        self.toml_file = toml_file
        self.streams = self.load_streams()
        
    def load_streams(self):
        try:
            with open(self.toml_file, 'rb') as f:
                data = tomli.load(f)
                return data.get('links', [])
        except Exception as e:
            print(f"Error loading streams: {e}")
            return []
    
    def get_all_streams(self):
        return self.streams
    
    def get_stream_by_name(self, name):
        for stream in self.streams:
            if stream['name'] == name:
                return stream
        return None