import pygame
from graphics_generator import *


'''
1. handle input to give to ben

2. receive visuals from brian

3. other stuff and features



'''
def draw_slider(screen, pos, size, val, min_val = 0, max_val=1):
    '''
    volume slider
    '''
    slider_rect = pygame.Rect(pos, size)
    pygame.draw.rect(screen, (100, 100, 100), slider_rect)

    handle_width = 20
    x = pos[0] + (val - min_val) / (max_val - min_val) * (size[0]-handle_width)
    handle_rect = pygame.Rect(x, pos[1], handle_width, size[1])

    pygame.draw.rect(screen, (200, 200, 200), handle_rect)
    return slider_rect

def draw_button(screen, text, position, size):
    font = pygame.font.Font(pygame.font.get_default_font(), 24)
    button_rect = pygame.Rect(position, size)
    pygame.draw.rect(screen, (50, 50, 50), button_rect)  
    text_surface = font.render(text, True, (255, 255, 255))  
    text_rect = text_surface.get_rect(center=button_rect.center)
    screen.blit(text_surface, text_rect)
    return button_rect

def startup_menu():
    pygame.init()
    screen = pygame.display.set_mode((1070, 600))
    clock = pygame.time.Clock()


    while True:
        screen.fill("black") 
        font = pygame.font.Font(pygame.font.get_default_font(), 36) 
        text = font.render("Drag and drop a file", True, "White")
        text_rect = text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))

        screen.blit(text, text_rect)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.DROPFILE:
                main(event.file, screen, clock)
            elif event.type == pygame.QUIT:
                pygame.quit()
                return





def main(song_path, screen, clock):

    try:
        # Load and process song data
        samplerate, duration_in_sec, num_of_channels, ydata, ydata_for_line = load_song(song_path)
        

        # Safety check
        if len(ydata) == 0 or len(ydata_for_line) == 0:
            print(f"Error: No data loaded from {song_path}")
            return

        xf_list, yf_list = process_frequency_data(ydata, samplerate)

        # Initialize pygame
        #screen, clock = init_pygame(song_path, samplerate)
        init_pygame(song_path, samplerate)
        pygame.mixer.music.play()


        # Initial state
        running = True
        playing = True
        count = 0
        start = 0
        y_origin = 500

        play_button_pos = (0, 500)
        play_button_size = (100, 50)

        song_path = None

        visualization_surface = None
        # Main loop

        screen_width, screen_height = screen.get_size()
        vis_height = 400
        vis_rect = pygame.Rect(0, 50, screen_width, vis_height)

        volume = 0.5
        volume_slider_rect = pygame.Rect(screen_width - 200, 10, 150, 20)
        while running:
            screen.fill((0, 0, 0))
            font = pygame.font.Font(pygame.font.get_default_font(), 20)
            
            volume_slider_rect = draw_slider(screen, (screen_width - 200, screen_height - 75), (150, 20), volume)
            volume_text = font.render(f"{int(volume * 100)}%", True, (255, 255, 255))
            screen.blit(volume_text, (screen_width - 250, screen_height - 75))

            button_text = "Pause" if playing else "Play"
            play_button = draw_button(screen, button_text, play_button_pos,
                                      play_button_size)
            for e in pygame.event.get():
                if e.type == py.QUIT:
                    running = False
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    if play_button.collidepoint(e.pos):
                        if playing:
                            pygame.mixer.music.pause()
                        else:
                            pygame.mixer.music.unpause()
                        playing = not playing
                elif e.type == pygame.MOUSEMOTION:
                    if e.buttons[0] and volume_slider_rect.collidepoint(e.pos):
                        volume = max(0, min(1, (e.pos[0] - volume_slider_rect.x)
                                             / volume_slider_rect.width))
                        pygame.mixer.music.set_volume(volume) 


            # Frame count to move the visualization at the same rate the song plays
            if playing:
                count += DELTA
#                count = pygame.mixer.music.get_pos() 

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
                    visualization_surface = pygame.Surface((screen_width, vis_height))
                    visualization_surface.fill((0,0,0))
                    visualization_surface = draw_frequency_spectrum(visualization_surface, xf, yf)
#                    pygame.draw.rect(visualization_surface, (100, 100, 100), vis_rect, 2)
                    screen.blit(visualization_surface, vis_rect.topleft)
                    # Start playing the song after first display is done
                    '''
                    if not pygame.mixer.music.get_busy():
                        pygame.mixer.music.play()
                    '''
                except Exception as e:
                    print(f"Error during visualization: {e}")


            
            if not playing and visualization_surface:
                screen.blit(visualization_surface, vis_rect.topleft)

            # Update display
            clock.tick(FPS)
            pygame.display.set_caption("FPS: " + str(int(clock.get_fps())))
            pygame.display.update()

        # Clean up
        pygame.quit()
    except Exception as e:
        print(f"Fatal error in visualizer: {e}")
        pygame.quit()



if __name__ == "__main__":
    startup_menu()
#    main("data/5mb.wav")