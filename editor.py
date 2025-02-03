import json
import os
import pickle
import shutil

import pygame
import sys
from config import *
from utils import *
from Brush import Brush
import importlib

REQUIREMENTS = ["File","Brush","Effect","Run","Undo","Export"]

# Initialize pygame
pygame.init()

FONT = pygame.font.Font(None, FONT_SIZE)

class Property:
    def __init__(self, label, value, type=None):
        self.rect = None
        self.label = label
        self.value = value
        self.type = type

    def position(self, x, y):
        self.rect = pygame.Rect(x, y,PROPERTY_WIDTH,PROPERTY_HEIGHT)

    def draw(self, screen):
        if self.type == "text":
            pygame.draw.rect(screen, GRAY, self.rect, border_radius=PROPERTY_CORNER_RADIUS)
            pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=PROPERTY_CORNER_RADIUS)
            text_surface = FONT.render(f"{self.label}: {self.value}", True, BLACK)
            text_rect = text_surface.get_rect(center=self.rect.center)
            screen.blit(text_surface, text_rect)
        elif self.type == "once":
            pygame.draw.rect(screen, BLACK, self.rect, border_radius=PROPERTY_CORNER_RADIUS)
            pygame.draw.rect(screen, GRAY, self.rect, 2, border_radius=PROPERTY_CORNER_RADIUS)
            text_surface = FONT.render(f"{self.label}", True, WHITE)
            text_rect = text_surface.get_rect(center=self.rect.center)
            screen.blit(text_surface, text_rect)
        elif self.type == "toggle":
            if self.value:
                pygame.draw.rect(screen, GREEN, self.rect, border_radius=PROPERTY_CORNER_RADIUS)
            else:
                pygame.draw.rect(screen, RED, self.rect, border_radius=PROPERTY_CORNER_RADIUS)
            pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=PROPERTY_CORNER_RADIUS)
            text_surface = FONT.render(f"{self.label}", True, BLACK)
            text_rect = text_surface.get_rect(center=self.rect.center)
            screen.blit(text_surface, text_rect)
        elif self.type == "title":
            pygame.draw.rect(screen, GRAY, self.rect, border_radius=PROPERTY_CORNER_RADIUS)
            pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=PROPERTY_CORNER_RADIUS)
            text_surface = FONT.render(f"Select {self.label}", True, BLACK)
            text_rect = text_surface.get_rect(center=self.rect.center)
            screen.blit(text_surface, text_rect)
        elif self.type == "color":
            pygame.draw.rect(screen, self.value, self.rect, border_radius=PROPERTY_CORNER_RADIUS)
            pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=PROPERTY_CORNER_RADIUS)
            text_surface = FONT.render(f"{self.label}", True, BLACK)
            text_rect = text_surface.get_rect(center=self.rect.center)
            screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.type == "toggle" or self.type == "once":
                    self.value = not self.value
                elif self.type == "text" or self.type=="title":
                    new_value = self.get_user_text(f"Enter new {self.label}:")
                    if new_value:
                        self.value = new_value
                elif self.type == "color":
                    new_value = self.get_user_color(f"Enter new {self.label}:")
                    if new_value:
                        self.value = new_value
                else:
                    return False
                return True
        return False

    def get_user_color(self,event):
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Select a Color")

        running = True
        selected_color = None

        while running:
            screen.fill((255, 255, 255))

            for row in range(GRID_ROWS):
                for col in range(GRID_COLS):
                    color = COLOR_GRID[row][col]
                    rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    pygame.draw.rect(screen, color, rect)
                    pygame.draw.rect(screen, (0, 0, 0), rect, 1)  # Border

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    row = y // CELL_SIZE
                    col = x // CELL_SIZE
                    if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
                        selected_color = COLOR_GRID[row][col]
                        running = False

        return selected_color

    def get_user_text(self, prompt):
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

        #pygame.display.set_caption("Brush Editor")
        return user_input

class Canvas():
    def __init__(self, file_property,x,y,width,height):
        self.file_path = file_property
        self.name = self.file_path.value.split("/")[-1].split(".")[0]

        self.image = None
        self.image_rect = None
        self.box = (x,y,width,height)
        self.modifications = 0
        self.copy2temp()

    def copy2temp(self):
        new_path = "temp/"+self.name+"."+str(self.modifications)+".png"
        shutil.copy(self.file_path.value, new_path)
        self.file_path.value = new_path

        self.update_image()

    def export_image(self):
        new_path = "images/" + self.name + "_" + str(self.modifications) + ".png"
        shutil.copy(self.file_path.value, new_path)

    def undo_image(self):
        self.modifications -= 1
        new_path = "temp/" + self.name + "." + str(self.modifications) + ".png"
        self.file_path.value = new_path
        self.update_image()

    def update_image(self,new_image = None):
        if new_image:
            self.modifications += 1
            new_path = "temp/" + self.name + "." + str(self.modifications) + ".png"
            self.file_path.value = new_path
            new_image.save(new_path, format="png")
            self.image = pygame.image.load(self.file_path.value)

        else:
            self.image = pygame.image.load(self.file_path.value)

        image_ratio = self.image.get_width() / self.image.get_height()
        max_width = self.box[2]  # SCREEN_WIDTH
        max_height = self.box[3]  # SCREEN_HEIGHT - (PROPERTY_HEIGHT + PROPERTY_MARGIN * 2)

        if max_width / max_height > image_ratio:
            new_height = max_height
            new_width = int(new_height * image_ratio)
        else:
            new_width = max_width
            new_height = int(new_width / image_ratio)

        self.image = pygame.transform.scale(self.image, (new_width, new_height))
        self.image_rect = self.image.get_rect(
            center=(self.box[0] + self.box[2] // 2, self.box[1] + self.box[3] // 2))


    def draw(self, screen):
        if self.image and self.image_rect:
            screen.blit(self.image, self.image_rect.topleft)



class App:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Brush Editor")

        self.running = True

        self.nshelf = 3
        self.shelves = [0] * self.nshelf

        self.buttons = {}
        self.req = REQUIREMENTS
        for req in self.req:
            self.add_button(req)

        self.canvas = self.add_canvas()

        self.brush_req = []
        self.effect_req = []
        self.brush = self.add_brush()
        self.add_effect()

    def add_canvas(self):
        y_offset = PROPERTY_HEIGHT * self.nshelf + PROPERTY_MARGIN * (self.nshelf + 1)

        self.canvas = Canvas(self.buttons["File"], PROPERTY_MARGIN, y_offset, SCREEN_WIDTH - PROPERTY_MARGIN * 2,
                             SCREEN_HEIGHT - y_offset - PROPERTY_MARGIN)
        return self.canvas

    def add_brush(self):
        #Clean up old brush buttons
        for k in self.brush_req:
            self.buttons.pop(k,None)
        self.shelves[1] = 0

        brush = importlib.import_module(self.buttons["Brush"].value)
        self.brush_req = brush.REQUIREMENTS
        for req in self.brush_req:
            self.add_button(req, True)

        self.brush = getattr(brush, self.buttons["Brush"].value)(*(self.buttons[k] for k in self.brush_req))
        return self.brush

    def add_effect(self):
        # Clean up old effect buttons
        for k in self.effect_req:
            self.buttons.pop(k, None)
            self.brush.properties.pop(k,None)
        self.shelves[2]=0

        effect = importlib.import_module("effects."+self.buttons["Effect"].value)
        self.effect_req = effect.REQUIREMENTS
        for req in self.effect_req:
            self.add_button(req, True)
            if req in self.buttons:
                self.brush.add_property(self.buttons[req])

    def add2shelf(self,y,prop: Property):
        x = self.shelves[y]
        prop.position(PROPERTY_MARGIN * (x + 1) + PROPERTY_WIDTH * x, PROPERTY_MARGIN * (y + 1) + PROPERTY_HEIGHT * y)
        self.shelves[y] +=1

    def add_button(self,label,replace = True):
        if label in self.buttons.keys() and not replace:
            return None

        match label:
            case "Effect":
                self.buttons[label] = Property("Effect", "QuantumBlurFull",type = "title")
                self.add2shelf(0,self.buttons[label])
            case "Brush":
                self.buttons[label] = Property("Brush", "Brush", type="title")
                self.add2shelf(0, self.buttons[label])
            case "Color":
                self.buttons[label] = Property("Color", (255,255,255),type = "color")
                self.add2shelf(2, self.buttons[label])
            case "Radius":
                self.buttons[label] = Property("Radius", "10",type = "text")
                self.add2shelf(1, self.buttons[label])
            case "Strength":
                self.buttons[label] = Property("Strength", "0.5", type="text")
                self.add2shelf(2, self.buttons[label])
            case "File":
                self.buttons[label] = Property("File", "images/spiral.png",type="title")
                self.add2shelf(0, self.buttons[label])
            case "Undo":
                self.buttons[label] = Property("Undo", False, type="once")
                self.add2shelf(0, self.buttons[label])
            case "Status":
                self.buttons[label] = Property("Status", True, type="toggle")
                self.add2shelf(1, self.buttons[label])
            case "Run":
                self.buttons[label] = Property("Run", False, type="once")
                self.add2shelf(0, self.buttons[label])
            case "Export":
                self.buttons[label] = Property("Export", False, type="once")
                self.add2shelf(0, self.buttons[label])
            case _:
                print(f"Label {label} is not yet implemented")
                return None

    def clean_directory(self,directory: str):
        """
        Removes all files and subdirectories inside the given directory.

        :param directory: Path to the directory to clean.
        """
        if not os.path.exists(directory):
            print(f"Directory '{directory}' does not exist.")
            return

        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)  # Remove file or symbolic link
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)  # Remove directory and contents
            except Exception as e:
                print(f"Failed to delete {item_path}: {e}")

        print(f"Directory '{directory}' has been cleaned.")

    def run(self):
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                event_handled = False
                for prop in self.buttons.values():
                    if prop.handle_event(event):
                        match prop.label:
                            case "Run":
                                if self.buttons["Run"].value:  # When Run is activated
                                    self.brush.run_brush(self.canvas, self.buttons["Effect"].value)
                                    self.buttons["Run"].value = False
                            case "Brush":
                                self.add_brush()
                                event_handled = True
                                break
                            case "Effect":
                                self.add_effect()
                                event_handled = True
                                break
                            case "File":
                                self.add_canvas()
                                self.brush.reset()
                                event_handled = True
                                break
                            case "Undo":
                                self.canvas.undo_image()
                                self.buttons["Undo"].value = False
                            case "Export":
                                self.canvas.export_image()
                                self.buttons["Export"].value = False

                        event_handled = True

                if not event_handled:
                    self.brush.handle_event(event)

            self.brush.update()

            self.screen.fill(WHITE)

            self.canvas.draw(self.screen)
            self.brush.draw(self.screen, mouse_pos)
            for button in self.buttons.values():
                button.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
if __name__ == "__main__":
    app = App()
    app.run()
    app.clean_directory('temp/')
