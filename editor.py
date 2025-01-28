import json
import pickle
import pygame
import sys
from config import *
from utils import *
from brush import Brush

# Initialize pygame
pygame.init()

FONT = pygame.font.Font(None, FONT_SIZE)

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

        #pygame.display.set_caption("Brush Editor")
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
            Property(PROPERTY_MARGIN * 4 + PROPERTY_WIDTH * 3, PROPERTY_MARGIN, PROPERTY_WIDTH, PROPERTY_HEIGHT, "File", ""),
            Property(PROPERTY_MARGIN * 5 + PROPERTY_WIDTH * 4, PROPERTY_MARGIN, PROPERTY_WIDTH, PROPERTY_HEIGHT, "Effect",
                     "Basic.py"),
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
