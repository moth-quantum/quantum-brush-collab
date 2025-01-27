import json

import pygame
import sys
import numpy as np
import subprocess
from PIL import Image

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)

# Property dimensions
PROPERTY_WIDTH = 150
PROPERTY_HEIGHT = 30
PROPERTY_MARGIN = 10
PROPERTY_CORNER_RADIUS = 10
FONT = pygame.font.Font(None, 24)


def apply_mask(array, mask):
    # Validate array dimensions
    if array.ndim != 3 or array.shape[-1] != 4:
        raise ValueError("The input array must have 3 dimensions, and the last dimension must be of size 4.")

    # Validate mask dimensions
    if mask.shape != array.shape[:2]:
        raise ValueError("The mask must have the same shape as the first two dimensions of the array.")

    # Set the last value to 0 where the mask is False
    array[~mask, -1] = 0  # Modify the last value directly

    return array



def interpolate_points(points, num_points):
    # List to store the resulting interpolated points
    interpolated = []

    # Calculate the total number of segments between points
    total_segments = len(points) - 1

    # Total number of points to generate
    total_points = num_points

    # Generate the points
    for i in range(total_segments):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]

        # Calculate the number of points between this pair of points
        points_in_segment = total_points // total_segments
        for j in range(points_in_segment):
            t = j / points_in_segment
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t
            interpolated.append((x, y))

    # Add the last point
    interpolated.append(points[-1])

    # If we have fewer than num_points (due to division rounding), add more points
    while len(interpolated) < total_points:
        interpolated.append(points[-1])

    return interpolated


def apply_circle(mask, x, y, radius):
    # Get the shape of the mask
    height, width = mask.shape
    cx = int(x)
    cy = int(y)
    r = int(radius)

    # Loop over the bounding box around the center (cx, cy)
    for x in range(max(0, cx - r), min(width, cx + r + 1)):
        for y in range(max(0, cy - r), min(height, cy + r + 1)):
            # Check if the point (x, y) is within the circle
            if (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2:
                mask[y,x] = 1  # Set the point to 1
    return mask


def rescale_coordinates(surface_rect, coords):
    # Get the width and height of the surface
    surface_width = surface_rect.width
    surface_height = surface_rect.height

    if isinstance(coords, tuple):
        rescaled_x = max(0, min(surface_width, coords[0] - surface_rect.x))
        rescaled_y = max(0, min(surface_height, coords[1] - surface_rect.y))

        return rescaled_x, rescaled_y

    elif isinstance(coords, list):
        return [rescale_coordinates(surface_rect,crd) for crd in coords]



class Brush:
    def __init__(self, *properties):
        self.properties = {property.label: property for property in properties}
        self.brush_path = []
        self.box = None
        self.image = None
        self.image_rect = None

    def update_brush(self):
        if not self.properties["Active"].value:
            self.brush_path = []
            self.box = None

        # Load image if File property is set
        file_path = self.properties["File"].value
        if file_path:
            try:
                self.image = pygame.image.load("images/"+file_path)
                image_ratio = self.image.get_width() / self.image.get_height()
                max_width = SCREEN_WIDTH
                max_height = SCREEN_HEIGHT - (PROPERTY_HEIGHT + PROPERTY_MARGIN * 2)

                if max_width / max_height > image_ratio:
                    new_height = max_height
                    new_width = int(new_height * image_ratio)
                else:
                    new_width = max_width
                    new_height = int(new_width / image_ratio)

                self.image = pygame.transform.scale(self.image, (new_width, new_height))
                self.image_rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, (SCREEN_HEIGHT + PROPERTY_HEIGHT) // 2))
            except pygame.error:
                print(f"Unable to load image: {file_path}")
                self.image = None
                self.image_rect = None

    def handle_event(self, event):
        if self.properties["Active"].value and self.image and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.brush_path.append((mouse_x, mouse_y))
            self.update_box()
            return True
        return False

    def update_box(self):
        if not self.brush_path:
            self.box = None
            return

        radius = int(self.properties["Radius"].value)
        x_coords = [p[0] for p in self.brush_path]
        y_coords = [p[1] for p in self.brush_path]
        self.box = (
            min(x_coords) - radius, min(y_coords) - radius,
            max(x_coords) + radius + 1, max(y_coords) + radius + 1
        )

    def run_brush(self):
        if not self.image or not self.box:
            print("No valid image or box to process.")
            return

        # Extract the portion of the image within the bounding box
        box_left, box_bottom, box_right, box_top = self.box
        box_left, box_bottom = rescale_coordinates(self.image_rect, (box_left, box_bottom))
        box_right, box_top = rescale_coordinates(self.image_rect, (box_right, box_top))

        # Convert the surface to an array for manipulation
        image_array = pygame.surfarray.pixels3d(self.image).swapaxes(0, 1)
        alpha_array = pygame.surfarray.pixels_alpha(self.image).swapaxes(0, 1)

        # Crop the image region
        cropped_image = image_array[box_bottom:box_top,box_left:box_right]

        # Create a mask to apply radius-based transparency
        radius = int(self.properties["Radius"].value)
        mask = np.zeros(alpha_array.shape, dtype=np.uint8)
        path = rescale_coordinates(self.image_rect, self.brush_path)

        for x,y in interpolate_points(path,100):
            mask = apply_circle(mask,x,y,radius)

        # Apply the mask to create transparency
        mask = mask.astype(bool)
        cropped_mask = mask[box_bottom:box_top,box_left:box_right]

        effect_points = [ [point[1]-box_top, point[0] - box_left] for point in path]
        effect_image = cropped_image.tolist()
        effect_params = json.dumps({"image": effect_image, "mask":cropped_mask.tolist(),"points": effect_points})


        effect_path = "effects/" + self.properties["Effect"].value
        result = subprocess.run(['python', effect_path,effect_params], capture_output=True, text=True)
        updated_image = np.array(json.loads(result.stdout))

        image_array[mask] = updated_image[cropped_mask]

        updated_image_pil = Image.fromarray(np.dstack((image_array,alpha_array)), mode="RGBA")

        self.properties["File"].value = "updated_"+self.properties["File"].value
        updated_image_pil.save("images/"+self.properties["File"].value)

        # Reset the brush
        self.properties["Active"].value = False
        self.update_brush()

    def draw(self, screen, mouse_pos):
        # Draw the image if it exists (after the brush path)
        if self.image and self.image_rect:
            screen.blit(self.image, self.image_rect.topleft)

        # Draw the brush cursor
        color = pygame.Color(self.properties["Color"].value)
        radius = int(self.properties["Radius"].value)
        color.a = int(float(self.properties["Strength"].value) * 255)

        # Draw the path as lines
        if len(self.brush_path) > 1:
            pygame.draw.lines(screen, color, False, self.brush_path, radius)

        pygame.draw.circle(screen, color, mouse_pos, radius)


class Property:
    def __init__(self, x, y, width, height, label, value, toggle=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.value = value
        self.toggle = toggle

    def draw(self, screen):
        pygame.draw.rect(screen, GRAY, self.rect, border_radius=PROPERTY_CORNER_RADIUS)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=PROPERTY_CORNER_RADIUS)
        text_surface = FONT.render(f"{self.label}: {self.value}", True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.toggle:
                    self.value = not self.value
                else:
                    new_value = self.get_user_input(f"Enter new {self.label}:")
                    if new_value:
                        self.value = new_value

                return True
        return False

    def get_user_input(self, prompt):
        pygame.display.set_caption(prompt)
        user_input = ""
        input_active = True

        while input_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        input_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        user_input = user_input[:-1]
                    else:
                        user_input += event.unicode

            pygame.display.get_surface().fill(WHITE)

            prompt_surface = FONT.render(prompt, True, BLACK)
            pygame.display.get_surface().blit(prompt_surface, (20, SCREEN_HEIGHT // 2 - 40))

            input_surface = FONT.render(user_input, True, BLACK)
            pygame.draw.rect(pygame.display.get_surface(), GRAY, (20, SCREEN_HEIGHT // 2, SCREEN_WIDTH - 40, 30))
            pygame.display.get_surface().blit(input_surface, (25, SCREEN_HEIGHT // 2 + 5))

            pygame.display.flip()

        pygame.display.set_caption("Brush Editor")
        return user_input

class App:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Brush Editor")

        self.running = True

        # Initialize properties
        self.properties = [
            Property(PROPERTY_MARGIN, PROPERTY_MARGIN, PROPERTY_WIDTH, PROPERTY_HEIGHT, "Color", "white"),
            Property(PROPERTY_MARGIN * 2 + PROPERTY_WIDTH, PROPERTY_MARGIN, PROPERTY_WIDTH, PROPERTY_HEIGHT, "Radius", "10"),
            Property(PROPERTY_MARGIN * 3 + PROPERTY_WIDTH * 2, PROPERTY_MARGIN, PROPERTY_WIDTH, PROPERTY_HEIGHT, "Strength", "0.5"),
            Property(PROPERTY_MARGIN * 4 + PROPERTY_WIDTH * 3, PROPERTY_MARGIN, PROPERTY_WIDTH, PROPERTY_HEIGHT, "File", "test.png"),
            Property(PROPERTY_MARGIN * 5 + PROPERTY_WIDTH * 4, PROPERTY_MARGIN, PROPERTY_WIDTH, PROPERTY_HEIGHT, "Effect",
                     "RemoveAlpha.py"),
            Property(PROPERTY_MARGIN * 6 + PROPERTY_WIDTH * 5, PROPERTY_MARGIN, PROPERTY_WIDTH, PROPERTY_HEIGHT, "Active", True, toggle=True)
        ]

        # Initialize brush with properties
        self.brush = Brush(*self.properties)

        # Initialize additional buttons
        self.run_button = Property(PROPERTY_MARGIN * 7 + PROPERTY_WIDTH * 6, PROPERTY_MARGIN, PROPERTY_WIDTH, PROPERTY_HEIGHT, "Run", False, toggle=True)

    def run(self):
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                event_handled = False
                for prop in self.properties:
                    if prop.handle_event(event):
                        event_handled = True

                if self.run_button.handle_event(event):
                    if self.run_button.value:  # When Run is activated
                        self.brush.run_brush()
                        self.run_button.value = False
                    event_handled = True

                if not event_handled:
                    self.brush.handle_event(event)

            self.brush.update_brush()
            self.screen.fill(WHITE)

            self.brush.draw(self.screen, mouse_pos)

            for prop in self.properties:
                prop.draw(self.screen)

            self.run_button.draw(self.screen)


            pygame.display.flip()

        pygame.quit()
if __name__ == "__main__":
    app = App()
    app.run()
