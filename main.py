import pygame


def main():

    running = True 
    screen = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()
    fps = 30
    pygame.display.set_caption('Sound Visualizer')
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False


        clock.tick(fps)

    #game is exited
    pygame.quit()


if __name__ == "__main__":
    main()