import math

import numpy as np
import pygame as py
from PIL.ImageChops import screen

from audio_processor import *
from constants import *


FPS = 60
VALUES_PER_SECOND = 20
DELTA = VALUES_PER_SECOND / FPS

def init_pygame(song_path, samplerate):
    """Initialize pygame and load the song."""
#    py.init()
    py.mixer.init(samplerate, -16, 1, 1024)

    # draw a 600x600 display
#    screen = py.display.set_mode((600, 600))
#   clock = py.time.Clock()

    # load the song to play with the animation
    py.mixer.music.load(song_path)
#    return screen, clock
def draw_frequency_spectrum(screen, xf, yf, color="BLUE"):
    """Draw the frequency spectrum visualization."""
    # Make sure we have enough data points
#    height = 300
    height = screen.get_height()
    width = screen.get_width() 

    max_y = max(yf) if max(yf) > 0 else 1
    min_y = min(yf)
 

    surface = py.Surface((width, height))
    surface.fill((0, 0, 0))
    #idk what below means

            # Use available points or fill with zeros
    points_count = min(len(xf), len(yf), 1000)
    points = []

    for i in range(points_count):
        if i < len(xf) and i < len(yf):
            try:
                #x_val = 10 + xf[i] / 40 if not np.isnan(xf[i]) else 10
                x_val = (i/points_count) * width
                #y_val = height - (yf[i] / 30000)*height if not np.isnan(yf[i]) else height
                y_val = height - ((yf[i] - min_y) / (max_y - min_y)) * height * 0.9
                points.append((x_val, y_val))
            except (TypeError, ValueError):
                points.append((0, height))
        else:
            # We have enough points
            try:
                points = [(10 + xf[i] / 40, height - yf[i] / 30000) for i in range(1000)]
            except (TypeError, ValueError, ZeroDivisionError):
                # Fallback if calculation fails
                points = [(10 + i, height) for i in range(1000)]

    # Add closing points for the polygon
    try:
        if len(xf) > 0:
            points.append((max(xf) / 40, height))
        else:
            points.append((10, height))
    except (ValueError, TypeError):
        points.append((10, height))


    points.append((0, height))

    # Draw the polygon if we have at least 3 points
    if len(points) >= 3:
        color_values = COLOR_MAPPING.get(color)
        print(color_values)
        py.draw.polygon(surface, color_values, points)
        py.draw.lines(surface, (255, 255, 255), True, points, 1)
    return surface


def draw_frequency_spectrum_circles(screen, xf, yf, color="BLUE"):
    """Draw the frequency spectrum visualization as three separate circular arcs for low, medium, and high frequencies."""
    # Setup dimensions
    width = screen.get_width()
    height = screen.get_height()

    # Define centers for our three circles
    centers = [
        (width // 4, height // 2),  # Low frequencies (left)
        (width // 2, height // 2),  # Medium frequencies (center)
        (width * 3 // 4, height // 2)  # High frequencies (right)
    ]

    # Max radius for each circle (slightly smaller to fit three circles)
    max_radius = int(min(width // 4, height // 2) * 0.8)

    # Create a new surface
    surface = py.Surface((width, height))
    surface.fill((0, 0, 0))

    # Make sure we have data
    if len(yf) == 0:
        return surface

    # Split the frequency data into three bands (low, medium, high)
    part = len(yf) // 3
    freq_bands = [
        yf[:part],  # Low frequencies
        yf[part:2 * part],  # Medium frequencies
        yf[2 * part:],  # High frequencies
    ]

    xf_bands = [
        xf[:part],  # Low frequencies x values
        xf[part:2 * part],  # Medium frequencies x values
        xf[2 * part:],  # High frequencies x values
    ]

    # Draw each frequency band as a separate circle
    for i, (band_xf, band_yf) in enumerate(zip(xf_bands, freq_bands)):
        # No data
        if len(band_yf) == 0:
            continue

        # Figure out which center to put data in
        center_x, center_y = centers[i]

        # Normalize the data for this band, this would determine the amplitude of the radius
        max_y = max(band_yf) if band_yf else 0
        min_y = min(band_yf) if band_yf else 0
        normalized_data = [(y - min_y) / (max_y - min_y) if max_y > min_y else 0 for y in band_yf]

        # Number of points to display (use fewer points for smoother circle)
        points_count = 360

        # Calculate points in a full circle
        points = []
        for j in range(points_count):
            if j < len(band_xf) and j < len(normalized_data):
                try:
                    # Convert to polar coordinates - full circle (0 to 2π)
                    angle = 2 * math.pi * (j / points_count)

                    # Get the data point index proportional to the angle
                    data_idx = int((j / points_count) * len(normalized_data))
                    # In case of overflow, set it to the last index
                    if data_idx >= len(normalized_data):
                        data_idx = len(normalized_data) - 1

                    # Normalize amplitude value
                    normalized_y = normalized_data[data_idx]

                    # Calculate radius based on frequency amplitude (higher amplitude = larger radius)
                    # Increased minimum radius to 30% for better visibility
                    radius = max_radius * (0.3 + normalized_y * 0.7)

                    # Convert to cartesian coordinates
                    x_val = center_x + radius * math.cos(angle)
                    y_val = center_y + radius * math.sin(angle)

                    points.append((x_val, y_val))
                except (TypeError, ValueError):
                    continue

        # Draw filled polygon if we have enough points
        if len(points) >= 3:
            # Get color
            color_values = COLOR_MAPPING.get(color)
            py.draw.polygon(surface, color_values, points)
            # Draw outlines for better visibility
            py.draw.lines(surface, (255, 255, 255), True, points, 1)

    return surface


def draw_frequency_spectrum_light_spots(screen, xf, yf):
    """
    Draw a visualization where frequencies are represented as glowing light spots
    that vary in size and brightness based on frequency data.
    """
    # Setup dimensions
    width = screen.get_width()
    height = screen.get_height()

    # Create a new surface
    surface = py.Surface((width, height))
    surface.fill((0, 0, 0))  # Black background

    # Make sure we have data
    if len(yf) == 0 or max(yf) <= 0:
        return surface

    # Normalize frequency data, this would determine the glow radius, by getting the data in the 0 to 1 range
    max_y = max(yf)
    min_y = min(yf)
    normalized_data = [(y - min_y) / (max_y - min_y) if max_y > min_y else 0 for y in yf]

    # Create a reduced set of data samples to work with
    # Reduced sample size to 50
    sample_count = 50  # This controls the number of light spots
    samples = []
    for i in range(sample_count):
        idx = int(i * len(normalized_data) / sample_count)
        if idx < len(normalized_data):
            samples.append(normalized_data[idx])

    # Generate fixed positions for the light spots
    import random
    random.seed(42)  # Fixed seed for consistency between frames

    spot_positions = []
    spot_colors = []
    for _ in range(sample_count):
        x = random.randint(0, width)
        y = random.randint(0, height)
        spot_positions.append((x, y))

        # Generate random base color for this spot
        r = random.randint(50, 255)
        g = random.randint(50, 255)
        b = random.randint(50, 255)
        spot_colors.append((r, g, b))

    # Draw each light spot based on the
    for i, value in enumerate(samples):
        if i < len(spot_positions):
            x, y = spot_positions[i]
            base_color = spot_colors[i]

            # Size based on frequency (larger for higher frequencies)
            size = int(5 + value * 40)  # Min size 5, max size 45

            # Brightness based on frequency
            brightness = 0.3 + value * 0.7
            spot_color = (
                int(min(base_color[0] * brightness, 255)),
                int(min(base_color[1] * brightness, 255)),
                int(min(base_color[2] * brightness, 255))
            )

            # Draw a filled circle for the spot
            py.draw.circle(surface, spot_color, (x, y), size)

            # Draw a filled circle for the spot
            py.draw.circle(surface, spot_color, (x, y), size)

            # Add one glow effect with a single glow circle
            glow_size = size + 5  # The glow size is larger than the spot
            glow_alpha = 100  # Constant alpha value for the glow

            # Create a transparent surface for the glow
            glow_surface = py.Surface((glow_size * 2, glow_size * 2), py.SRCALPHA)
            glow_surface.fill((0, 0, 0, 0))  # Transparent background

            # Draw the glow circle
            glow_color = (spot_color[0], spot_color[1], spot_color[2], glow_alpha)
            py.draw.circle(glow_surface, glow_color, (glow_size, glow_size), glow_size)

            # Blit the glow surface onto the main surface
            surface.blit(glow_surface, (x - glow_size, y - glow_size), special_flags=py.BLEND_RGBA_ADD)

    return surface

'''
maybe need folder instead of 1 file lol


i think steps are
1. take processed data from ben
2. ???
3. 
4. return visuals(as a pygame surface?) to gary to blit it(?, new to pygame so idk)

'''