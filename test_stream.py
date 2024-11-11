from stream_manager import StreamManager
import time

print("Creating StreamManager...")
sm = StreamManager(80)  # Set volume to 80%

print("\nTrying to play link1 (nature radio)...")
sm.play_stream('link1')  # Test with nature radio stream

print("\nWaiting 10 seconds...")
time.sleep(10)

print("\nChanging volume to 50%...")
sm.set_volume(50)
time.sleep(5)

print("\nChanging volume to 100%...")
sm.set_volume(100)
time.sleep(5)

print("\nStopping stream...")
sm.stop_stream() 