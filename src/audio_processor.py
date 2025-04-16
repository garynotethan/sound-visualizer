'''
1. load sound file
2. process it (?)
3. pass it to brian in a meaningful way

'''
from scipy.io import wavfile
import librosa
import numpy as np
from scipy.fft import fft, fftfreq
import scipy.signal
import matplotlib.pyplot as plt

VALUES_PER_SECOND = 20

def load_song(song_path):
    """Load and process audio data from the song file."""
    samplerate, data = wavfile.read(song_path)
    duration_in_sec = librosa.get_duration(path=song_path)

    # Determine number of channels
    try:
        _, num_of_channels = data.shape
    except:
        num_of_channels = 1

    # Process audio data based on channels
    if num_of_channels == 1:
        ydata_for_line = list(data)
        ydata = list(np.array_split(data, VALUES_PER_SECOND * duration_in_sec))
    else:
        ydata_for_line = list(data[:, 0])
        ydata = list(np.array_split(data[:, 1], VALUES_PER_SECOND * duration_in_sec))

    return samplerate, duration_in_sec, num_of_channels, ydata, ydata_for_line

def process_frequency_data(ydata, samplerate):
    """Process frequency data from audio samples."""
    xf_list = []
    yf_list = []

    # Getting the frequency spectrum
    for data_chunk in ydata:
        # Handle empty or zero arrays
        if len(data_chunk) == 0 or np.all(data_chunk == 0):
            # Create dummy data if the chunk is empty or all zeros
            n = 2048 if len(data_chunk) == 0 else data_chunk.size
            xf_list.append([0] * n)
            yf_list.append([0] * n)
            continue

        try:
            # Safe normalization
            max_val = np.max(np.abs(data_chunk))
            if max_val > 0:
                normalized_data = np.int16((data_chunk / max_val) * 32767)
            else:
                normalized_data = np.int16(data_chunk)

            n = data_chunk.size

            yf = list(np.abs(fft(normalized_data)))
            xf = list(fftfreq(n, 1 / samplerate))

            xf_list.append(xf)
            yf_list.append(yf)
        except Exception as e:
            print(f"Error processing frequency data: {e}")
            # Add empty data as fallback
            n = data_chunk.size if hasattr(data_chunk, 'size') else 2048
            xf_list.append([0] * n)
            yf_list.append([0] * n)

    return xf_list, yf_list

# Detect beats in audio samples using energy
"""
Parameters:
- samples: List of audio samples
- sample_rate: Sampling rate in Hz (default: 44100)
- window_size: Number of samples per analysis window (default: 1024)
- hop_size: Number of samples between consecutive windows (default: 512)
- sensitivity: Beat detection sensitivity (higher = fewer beats) (default: 1.3)

Returns:
- List of sample indices where beats were detected
"""
def detect_beats(samples, sample_rate=44100, window_size=1024, hop_size=512, sensitivity=1.3):

    beat_idxs = []
    avg_energy = 0.0
    cooldown_in_frames = int(0.1 * sample_rate / hop_size)
    init_frames = max(1, int(0.1 * sample_rate / hop_size))
    energy_buffer = []
    cooldown_counter = 0

    for i in range(0, len(samples) - window_size + 1, hop_size):

        window = samples[i:i+window_size]
        energy = sum(sample**2 for sample in window) / window_size  # Normalized energy

        # Initialization phase
        if len(energy_buffer) < init_frames:
            energy_buffer.append(energy)
            if len(energy_buffer) == init_frames:
                avg_energy = sum(energy_buffer) / init_frames
            continue

        # Apply cooldown period
        if cooldown_counter > 0:
            cooldown_counter -= 1
            avg_energy = 0.9 * avg_energy + 0.1 * energy
            continue

        # Update moving average
        avg_energy = 0.9 * avg_energy + 0.1 * energy

        # Detect beat
        if energy > avg_energy * sensitivity:
            beat_idxs.append(i)  # The start of the window is the start of the beat
            cooldown_counter = cooldown_in_frames

    return beat_idxs

# Detect significant changes in average frequency content of audio
"""
Parameters:
- samples: Audio samples (list or numpy array)
- sample_rate: Sampling rate in Hz (default: 44100)
- window_size: FFT window size (default: 2048)
- hop_size: Samples between consecutive windows (default: 1024)
- sensitivity: Relative change threshold (0-1) (default: 0.3)

Returns:
- List of sample indices where significant frequency changes occurred
"""
def detect_frequency_changes(samples, sample_rate=44100, window_size=2048, hop_size=1024, sensitivity=0.3):

    freqchange_idxs = []
    prev_avg_freq = None
    cooldown_frames = int(0.2 * sample_rate / hop_size)
    cooldown_counter = 0

    # Frequency bins for FFT
    freqs = np.fft.rfftfreq(window_size, 1/sample_rate)
    freq_mask = (freqs >= 20) & (freqs <= 20000)
    valid_freqs = freqs[freq_mask]

    for i in range(0, len(samples) - window_size + 1, hop_size):
        window = samples[i:i+window_size]

        # Skip low-energy windows
        window_energy = np.mean(np.square(window))
        if window_energy < 0.01:
            continue

        # Compute FFT and spectral centroid
        fft = np.fft.rfft(window)
        magnitudes = np.abs(fft)[freq_mask]

        if np.sum(magnitudes) == 0:
            continue  # Skip zero-magnitude windows

        avg_freq = np.sum(valid_freqs * magnitudes) / np.sum(magnitudes)

        # Initialize first value
        if prev_avg_freq is None:
            prev_avg_freq = avg_freq
            continue

        # Apply cooldown
        if cooldown_counter > 0:
            cooldown_counter -= 1
            prev_avg_freq = 0.9 * prev_avg_freq + 0.1 * avg_freq
            continue

        # Calculate relative change
        relative_change = abs(avg_freq - prev_avg_freq) / prev_avg_freq

        if relative_change > sensitivity:
            freqchange_idxs.append(i)
            cooldown_counter = cooldown_frames
            prev_avg_freq = avg_freq # Reset reference to current value
        else:
            prev_avg_freq = 0.9 * prev_avg_freq + 0.1 * avg_freq # Update moving average

    return freqchange_idxs
