import numpy as np
import pygame as py
from audio_processor import *


FPS = 60
VALUES_PER_SECOND = 20
DELTA = VALUES_PER_SECOND / FPS

def init_pygame(song_path, samplerate):
    """Initialize pygame and load the song."""
    py.init()
    py.mixer.init(samplerate, -16, 1, 1024)

    # draw a 600x600 display
    screen = py.display.set_mode((600, 600))
    clock = py.time.Clock()

    # load the song to play with the animation
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
    run_visualizer("data/5mb.wav")

'''
maybe need folder instead of 1 file lol


i think steps are
1. take processed data from ben
2. ???
3. 
4. return visuals(as a pygame surface?) to gary to blit it(?, new to pygame so idk)

'''