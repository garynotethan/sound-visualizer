
from scipy.io import wavfile
import librosa
import numpy as np
from scipy.fft import fft, fftfreq

from src.audio_processor import analyze_rhythm, load_song

# Load and process audio data from a song file

song_path = "./data/5mb.wav"

samplerate, duration_in_sec, num_of_channels, ydata, ydata_for_line = load_song(song_path)

analyze_rhythm(np.concatenate(ydata))

