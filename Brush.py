import pygame
import numpy as np
import pickle
import subprocess

from config import *
from utils import *
from PIL import Image

#List of brush-specific requirements
REQUIREMENTS = ["Status","Radius"]

class Brush:
    def __init__(self, *properties):
        self.label = "Normal Brush"
        self.properties = {property.label: property for property in properties}
        self.brush_path = []
        self.box = None

    def update(self):
        if not self.properties["Status"].value:
            self.brush_path = []
            self.box = None

    def add_property(self,property):
        self.properties[property.label] = property

    def handle_event(self, event):
        if self.properties["Status"].value and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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
            min(x_coords) - radius, max(y_coords) + radius,
            max(x_coords) + radius, min(y_coords) - radius
        )

    def run_brush(self,canvas,effect):
        # Extract the portion of the image within the bounding box
        box_left, box_bottom, box_right, box_top = self.box
        box_left, box_bottom = rescale_coordinates(canvas.image_rect, (box_left, box_bottom))
        box_right, box_top = rescale_coordinates(canvas.image_rect, (box_right, box_top))

        # Convert the surface to an array for manipulation
        image_array = pygame.surfarray.pixels3d(canvas.image)#.swapaxes(0, 1)
        alpha_array = pygame.surfarray.pixels_alpha(canvas.image)#.swapaxes(0, 1)

        # Crop the image region
        cropped_image = image_array[box_left:box_right+1,box_top:box_bottom+1]

        # Create a mask to apply radius-based transparency
        radius = int(self.properties["Radius"].value)
        mask = np.zeros(alpha_array.shape, dtype=np.uint8)
        path = rescale_coordinates(canvas.image_rect, self.brush_path)

        for x,y in interpolate_points(path,100):
            mask = apply_circle(mask,x,y,radius)

        # Crop the mask
        mask = mask.astype(bool)
        cropped_mask = mask[box_left:box_right+1,box_top:box_bottom+1]

        effect_params = {"Image": cropped_image,
                         "Mask": cropped_mask,
                         "Points": [(point[0] - box_left, point[1]-box_top) for point in path],
                         "Radius": radius}
        effect_params |= {prop: self.properties[prop].value for prop in self.properties}

        effect_id = str(np.random.randint(np.iinfo(np.int64).max))

        with open("temp/parameters_"+effect_id+".pkl", 'wb') as f:
            pickle.dump(effect_params, f)

        effect_path = "effects/" + effect + ".py"
        sp = subprocess.run(['python', effect_path,effect_id], capture_output=True, text=True)
        print(sp.stdout)
        print(sp.stderr)
        with open("temp/image_"+effect_id+".pkl", 'rb') as f:
            updated_image = pickle.load(f)

        #Apply mask to original image
        image_array[mask] = updated_image[cropped_mask]
        updated_image_pil = Image.fromarray(np.dstack((image_array,alpha_array)).swapaxes(0, 1), mode="RGBA")

        canvas.file.value = "up_"+canvas.file.value
        updated_image_pil.save("images/"+canvas.file.value,format="png")
        canvas.update_image()

        # Reset the brush
        self.properties["Status"].value = False
        self.update()

    def draw(self, screen, mouse_pos):
        # Draw the brush cursor
        color = pygame.Color("white")
        radius = int(self.properties["Radius"].value)

        # Draw the path as lines
        if self.brush_path:
            pygame.draw.circle(screen, color, self.brush_path[0], radius)
            if len(self.brush_path)>1:
                pygame.draw.lines(screen, color, False, self.brush_path, 2*radius)
                pygame.draw.circle(screen, color, self.brush_path[-1], radius)
        pygame.draw.circle(screen, color, mouse_pos, radius)

