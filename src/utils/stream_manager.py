import tomli

class StreamManager:
    def __init__(self, toml_file='config/streams.toml'):
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
        if not name:
            return None
        
        try:
            # Make sure we're working with a Stream object, not a dict
            for stream in self.streams:
                if isinstance(stream, dict):
                    if stream.get('name') == name:
                        return Stream(**stream)
                elif stream.name == name:
                    return stream
            return None
        except Exception as e:
            print(f"Error getting stream by name: {e}")
            return None

class Stream:
    def __init__(self, name, url, description=None, country=None, **kwargs):
        self.name = name
        self.url = url
        self.description = description or ""
        self.country = country or ""
        # Handle any additional fields from TOML
        for key, value in kwargs.items():
            setattr(self, key, value)