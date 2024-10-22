import vlc

# Create an instance of the VLC player
player = vlc.MediaPlayer()

# Define the URL of the radio stream
radio_stream_url = 'https://stream.spreeradio.de/spree-chill/mp3-192/'

# Set the media to the player
media = vlc.Media(radio_stream_url)
player.set_media(media)

# Play the media
player.play()

# Keep the program running to allow streaming
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
