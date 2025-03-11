'''
1. load sound file
2. process it (?)
3. pass it to brian in a meaningful way


'''
from scipy.io import wavfile
import librosa
import numpy as np
from scipy.fft import fft, fftfreq

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

