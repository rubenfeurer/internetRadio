from dataclasses import dataclass
from typing import Optional

@dataclass
class RadioStream:
    """Radio stream data model"""
    name: str
    url: str
    country: str
    location: str
    description: Optional[str] = None
    genre: Optional[str] = None
    language: Optional[str] = None
    bitrate: Optional[int] = None
    
    def __post_init__(self):
        """Validate required fields"""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Name is required and must be a string")
        if not self.url or not isinstance(self.url, str):
            raise ValueError("URL is required and must be a string")
        if not self.country or not isinstance(self.country, str):
            raise ValueError("Country is required and must be a string")
        if not self.location or not isinstance(self.location, str):
            raise ValueError("Location is required and must be a string") 