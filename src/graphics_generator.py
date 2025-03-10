from scipy.io import wavfile
import numpy as np
import pygame as py
from scipy.fft import fft, fftfreq
import librosa

VALUES_PER_SECOND = 20
FPS = 60
DELTA = VALUES_PER_SECOND / FPS


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


def init_pygame(song_path, samplerate):
    """Initialize pygame and load the song."""
    py.init()
    py.mixer.init(samplerate, -16, 1, 1024)

    screen = py.display.set_mode((600, 600))
    clock = py.time.Clock()

    py.mixer.music.load(song_path)

    return screen, clock


def draw_frequency_spectrum(screen, xf, yf):
    """Draw the frequency spectrum visualization."""
    # Make sure we have enough data points
    if len(xf) < 1000 or len(yf) < 1000:
        # Use available points or fill with zeros
        points_count = min(len(xf), len(yf), 1000)
        points = []

        for i in range(points_count):
            if i < len(xf) and i < len(yf):
                try:
                    x_val = 10 + xf[i] / 40 if not np.isnan(xf[i]) else 10
                    y_val = 300 - yf[i] / 30000 if not np.isnan(yf[i]) else 300
                    points.append((x_val, y_val))
                except (TypeError, ValueError):
                    points.append((10, 300))
    else:
        # We have enough points
        try:
            points = [(10 + xf[i] / 40, 300 - yf[i] / 30000) for i in range(1000)]
        except (TypeError, ValueError, ZeroDivisionError):
            # Fallback if calculation fails
            points = [(10 + i, 300) for i in range(1000)]

    # Add closing points for the polygon
    try:
        if len(xf) > 0:
            points.append((max(xf) / 40, 300))
        else:
            points.append((10, 300))
    except (ValueError, TypeError):
        points.append((10, 300))

    points.append((0, 300))

    # Draw the polygon if we have at least 3 points
    if len(points) >= 3:
        py.draw.polygon(screen, (100, 100, 255), points)


def draw_sound_line(screen, ydata_for_line, start, y_origin):
    """Draw the sound waveform line."""
    last_pos = (0, 0)
    data_length = len(ydata_for_line)

    for i in range(1000):
        # Check if the index is within the bounds of ydata_for_line
        index = min((i + start) * 10, data_length - 1)

        if index < 0:
            index = 0

        pos = (i * 6, y_origin - ydata_for_line[index] / 400)
        py.draw.line(screen, (255, 255, 255), pos, last_pos, 1)
        last_pos = pos

    # Calculate next start position, ensuring it won't go out of bounds next iteration
    next_start = start + int(data_length / 6000)  # More conservative increment

    # If we've reached the end, reset to beginning
    if next_start * 10 >= data_length:
        next_start = 0

    return next_start


def run_visualizer(song_path):
    """Main function to run the audio visualizer."""
    try:
        # Load and process song data
        samplerate, duration_in_sec, num_of_channels, ydata, ydata_for_line = load_song(song_path)

        # Safety check
        if len(ydata) == 0 or len(ydata_for_line) == 0:
            print(f"Error: No data loaded from {song_path}")
            return

        xf_list, yf_list = process_frequency_data(ydata, samplerate)

        # Initialize pygame
        screen, clock = init_pygame(song_path, samplerate)

        # Initial state
        running = True
        count = 0
        start = 0
        y_origin = 500

        # Main loop
        while running:
            screen.fill((0, 0, 0))

            for e in py.event.get():
                if e.type == py.QUIT:
                    running = False

            # Frame count to move the visualization at the same rate the song plays
            count += DELTA

            # Safety check for empty lists
            if not xf_list or not yf_list:
                print("Warning: Empty frequency data")
                continue

            # Get x and y axes of the spectrum for the current instant
            current_frame = min(int(count), len(xf_list) - 1)  # Prevent index out of range

            # Another safety check
            if current_frame < 0 or current_frame >= len(xf_list):
                current_frame = 0

            xf, yf = xf_list[current_frame], yf_list[current_frame]

            try:
                # Draw visualizations
                draw_frequency_spectrum(screen, xf, yf)
                start = draw_sound_line(screen, ydata_for_line, start, y_origin)

                # Start playing the song after first display is done
                if not py.mixer.music.get_busy():
                    py.mixer.music.play()
            except Exception as e:
                print(f"Error during visualization: {e}")

            # Update display
            clock.tick(FPS)
            py.display.set_caption("FPS: " + str(int(clock.get_fps())))
            py.display.update()

        # Clean up
        py.quit()
    except Exception as e:
        print(f"Fatal error in visualizer: {e}")
        py.quit()


# Example usage
if __name__ == "__main__":
    run_visualizer("samples/guitarloop60bpm2.wav")

'''
maybe need folder instead of 1 file lol


i think steps are
1. take processed data from ben
2. ???
3. 
4. return visuals(as a pygame surface?) to gary to blit it(?, new to pygame so idk)

'''