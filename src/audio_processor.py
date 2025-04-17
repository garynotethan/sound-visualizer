
from scipy.io import wavfile
import librosa
import numpy as np
from scipy.fft import fft, fftfreq

# Load and process audio data from .wav file
"""
Parameters:
- song_path: Path string to audio file
- samples_per_chunk: number of samples indicating the size of the chunks the audio will be split into (default: 2000)
Returns:
- samplerate: The sample rate of the audio file (Hz)
- duration_in_sec: Duration of the audio file (sec)
- num_of_channels: Number of channels encoded into the audio file
- ydata: A list of audio samples from the file split into chunks of length "samples_per_chunk"
- ydata_for_line: A list of audio samples from the file
"""
def load_song(song_path, samples_per_chunk=2000):

    # Get .wav file info
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
        ydata = list(np.array_split(data, samplerate * duration_in_sec / samples_per_chunk))
    else:
        ydata_for_line = list(data[:, 0]) # only take first channel
        ydata = list(np.array_split(data[:, 1], samplerate * duration_in_sec / samples_per_chunk))

    return samplerate, duration_in_sec, num_of_channels, ydata, ydata_for_line

# Process frequency data from audio samples
"""
Parameters:
- ydata: List of chunks of audio samples
- sample_rate: Sampling rate in Hz (default: 44100)
Returns:
- xf_list: List of chunks of samples frequencies
- yf_list: List of chunks of values for sampled frequencies
"""
def process_frequency_data(ydata, samplerate=44100):

    xf_list = []
    yf_list = []

    # Get frequency spectrum
    for data_chunk in ydata:

        # For empty or zero arrays
        if len(data_chunk) == 0 or np.all(data_chunk == 0):
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

            xf_list.append(list(fftfreq(data_chunk.size, 1 / samplerate))) # Obtain FFT sample frequencies
            yf_list.append(list(np.abs(fft(normalized_data)))) # Obtain sampled frequency values

        except Exception as e:
            print(f"Error processing frequency data: {e}")
            # Add empty data as fallback
            n = data_chunk.size if hasattr(data_chunk, 'size') else 2048
            xf_list.append([0] * n)
            yf_list.append([0] * n)

    return xf_list, yf_list

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
    freq_mask = (freqs >= 20) & (freqs <= 20000) # only keep the frequencies in the human hearing range
    valid_freqs = freqs[freq_mask]

    for i in range(0, len(samples) - window_size + 1, hop_size):
        window = samples[i:i+window_size]

        # Skip low-energy windows
        window_energy = np.mean(np.square(window))
        if window_energy < 0.01:
            continue

        # Compute FFT
        fft = np.fft.rfft(window)
        magnitudes = np.abs(fft)[freq_mask]

        # Skip zero-magnitude windows
        if np.sum(magnitudes) == 0:
            continue

        # Compute average frequency of the window
        avg_freq = np.sum(valid_freqs * magnitudes) / np.sum(magnitudes)

        # Make sure the value for the previous average frequency has a value
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

        # Add frequency index if the change is big enough
        if relative_change > sensitivity:
            freqchange_idxs.append(i)
            cooldown_counter = cooldown_frames
            prev_avg_freq = avg_freq # Reset reference frequency value
        else:
            prev_avg_freq = 0.9 * prev_avg_freq + 0.1 * avg_freq # Update moving average

    return freqchange_idxs

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
    init_frames = max(1, cooldown_in_frames) # Start after cooldown if cooldown comes after fill
    energy_buffer = []
    cooldown_counter = 0

    for i in range(0, len(samples) - window_size + 1, hop_size):

        window = samples[i:i+window_size]
        energy = sum(sample**2 for sample in window) / window_size  # Normalized energy

        # Initialization phase - gather energy values until there's enough to make an average
        if len(energy_buffer) < init_frames: # If we don't have enough energy values
            energy_buffer.append(energy) # Add the ones we just got to the buffer
            if len(energy_buffer) >= init_frames: # If we have enough, start the average
                avg_energy = sum(energy_buffer) / len(energy_buffer)
            continue

        # Update moving average
        avg_energy = 0.9 * avg_energy + 0.1 * energy

        # Move on to the next window if we're still in the cooldown
        if cooldown_counter > 0:
            cooldown_counter -= 1
            continue

        # Add beat if detected
        if energy > avg_energy * sensitivity:
            beat_idxs.append(i)  # Call the start of the window the start of the beat
            cooldown_counter = cooldown_in_frames

    return beat_idxs
