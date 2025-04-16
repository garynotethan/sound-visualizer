
import numpy as np
from src.audio_processor import load_song, detect_beats, detect_frequency_changes

# Load and process audio data from a song file

song_path = "./data/notes.wav"

samplerate, duration_in_sec, num_of_channels, ydata, ydata_for_line = load_song(song_path)

beats = detect_beats(ydata_for_line)
freqshifts = detect_frequency_changes(ydata_for_line)

print(beats)
print(freqshifts)
