import pygame

# Screen dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (46,139,87)
BACK_COLOR = (183,197,199)
# Property dimensions
PROPERTY_WIDTH = 190
PROPERTY_HEIGHT = 30
PROPERTY_MARGIN = 10
PROPERTY_CORNER_RADIUS = 10

FONT_SIZE = 24

GRID_ROWS = 7
GRID_COLS = 10
CELL_SIZE = 50

# Define base colors (7 hues)
BASE_COLORS = [
    (255, 0, 0),     # Red
    (255, 165, 0),   # Orange
    (255, 255, 0),   # Yellow
    (0, 255, 0),     # Green
    (0, 255, 255),   # Cyan
    (0, 0, 255),     # Blue
    (128, 0, 128),    # Purple
    (255,255,255)
]

# Function to generate color shades
def generate_shades(base_color, num_shades=10):
    shades = []
    for i in range(num_shades):
        factor = (i + 1) / num_shades
        shades.append((
            int(base_color[0] * factor),
            int(base_color[1] * factor),
            int(base_color[2] * factor)
        ))
    return shades

# Generate all colors for the grid
COLOR_GRID = [generate_shades(color, GRID_COLS) for color in BASE_COLORS]
