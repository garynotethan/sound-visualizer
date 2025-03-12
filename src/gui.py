import pygame
from graphics_generator import *

'''
1. handle input to give to ben

2. receive visuals from brian

3. other stuff and features



'''


def main(song_path):


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
                visualization_surface = draw_frequency_spectrum(screen, xf, yf)

                # Start playing the song after first display is done
                if not py.mixer.music.get_busy():
                    py.mixer.music.play()
            except Exception as e:
                print(f"Error during visualization: {e}")

            screen.blit(visualization_surface, (0, 0))

            # Update display
            clock.tick(FPS)
            py.display.set_caption("FPS: " + str(int(clock.get_fps())))
            py.display.update()

        # Clean up
        py.quit()
    except Exception as e:
        print(f"Fatal error in visualizer: {e}")
        py.quit()



if __name__ == "__main__":
    main("data/5mb.wav")