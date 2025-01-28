import pygame
import numpy as np
import pickle
import subprocess

from config import *
from utils import *
from PIL import Image

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

        color = pygame.Color(self.properties["Color"].value)
        color = [color.r,color.g,color.b]

        effect_params = {"Image": cropped_image.tolist(),
                         "Mask":cropped_mask.tolist(),
                         "Points": [[point[1]-box_top, point[0] - box_left] for point in path],
                         "Color": color}
        effect_id = "0"

        with open("temp/parameters_"+effect_id+".pkl", 'wb') as f:
            pickle.dump(effect_params, f)

        effect_path = "effects/" + self.properties["Effect"].value
        subprocess.run(['python', effect_path,effect_id], capture_output=True, text=True)

        with open("temp/image_"+effect_id+".pkl", 'rb') as f:
            updated_image = pickle.load(f)

        #Apply mask to original image
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
        if self.brush_path:
            pygame.draw.circle(screen, color, self.brush_path[0], radius)
            if len(self.brush_path)>1:
                pygame.draw.lines(screen, color, False, self.brush_path, 2*radius)
                pygame.draw.circle(screen, color, self.brush_path[-1], radius)

        pygame.draw.circle(screen, color, mouse_pos, radius)
