import json
import pickle
import pygame
import sys
from config import *
from utils import *
from Brush import Brush
import importlib

REQUIREMENTS = ["Run","Effect","File"]

# Initialize pygame
pygame.init()

FONT = pygame.font.Font(None, FONT_SIZE)

class Property:
    def __init__(self, label, value, type=None):
        self.rect = None
        self.label = label
        self.value = value
        self.type = type

    def position(self, x, y=None, width=None, height=None):
        if y is None:
            self.rect = pygame.Rect(PROPERTY_MARGIN * (x+1) + PROPERTY_WIDTH * x, PROPERTY_MARGIN, PROPERTY_WIDTH, PROPERTY_HEIGHT)
            return None

        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, screen):
        if self.type == "text":
            pygame.draw.rect(screen, GRAY, self.rect, border_radius=PROPERTY_CORNER_RADIUS)
            pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=PROPERTY_CORNER_RADIUS)
            text_surface = FONT.render(f"{self.label}: {self.value}", True, BLACK)
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

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.type == "toggle":
                    self.value = not self.value
                elif self.type == "text":
                    new_value = self.get_user_text(f"Enter new {self.label}:")
                    if new_value:
                        self.value = new_value
                else:
                    return False
                return True
        return False

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
    def __init__(self, file_property):
        self.file = file_property
        self.image = None
        self.image_rect = None
        self.update_image()

    def update_image(self):
        if self.file.value:
            try:
                self.image = pygame.image.load("images/" + self.file.value)
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
                self.image_rect = self.image.get_rect(
                    center=(SCREEN_WIDTH // 2, (SCREEN_HEIGHT + PROPERTY_HEIGHT) // 2))
            except pygame.error:
                print(f"Unable to load image: {self.file_path}")
                self.image = None
                self.image_rect = None
        else:
            print(f"Image path not set.")

    def draw(self, screen):
        if self.image and self.image_rect:
            screen.blit(self.image, self.image_rect.topleft)



class App:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Brush Editor")

        self.running = True
        self.buttons = {}
        self.req = ["File","Run","Brush","Effect"]
        for req in self.req:
            self.add_button(req)

        self.canvas = Canvas(self.buttons["File"])
        self.brush_req = []
        self.effect_req = []
        self.brush = self.add_brush()
        self.add_effect()

    def add_brush(self):
        #Clean up old brush buttons
        to_clean = [x for x in self.brush_req if x not in self.req + self.effect_req]
        for k in to_clean:
            self.buttons.pop(k,None)

        brush = importlib.import_module(self.buttons["Brush"].value)
        self.brush_req = brush.REQUIREMENTS
        for req in self.brush_req:
            self.add_button(req, False)

        self.brush = getattr(brush, self.buttons["Brush"].value)(*(self.buttons[k] for k in self.brush_req))
        return self.brush

    def add_effect(self):
        # Clean up old brush buttons
        to_clean = [x for x in self.effect_req if x not in self.req + self.brush_req]
        for k in to_clean:
            self.buttons.pop(k, None)
            self.brush.properties.pop(k,None)

        effect = importlib.import_module("effects."+self.buttons["Effect"].value)
        self.effect_req = effect.REQUIREMENTS
        for req in self.effect_req:
            self.add_button(req, False)
            if req in self.buttons:
                self.brush.add_property(self.buttons[req])

    def add_button(self,label,replace = True):
        if label in self.buttons.keys() and not replace:
            return None

        match label:
            case "Effect": self.buttons[label] = Property("Effect", "QuantumBlur",type = "text")
            case "Brush": self.buttons[label] = Property("Brush", "Brush", type="text")
            case "Color": self.buttons[label] = Property("Color", "white",type = "text")
            case "Radius": self.buttons[label] = Property("Radius", "10",type = "text")
            case "Strength": self.buttons[label] = Property("Strength", "0.5", type="text")
            case "File": self.buttons[label] = Property("File", "test.png",type="text")
            case "Status": self.buttons[label] = Property("Status", True, type="toggle")
            case "Run": self.buttons[label] = Property("Run", False, type="toggle")
            case _:
                print(f"Label {label} is not yet implemented")
                return None

        self.buttons[label].position(len(self.buttons)-1)

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
                                self.canvas.update_image()
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
