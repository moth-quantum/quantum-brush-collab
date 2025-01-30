import sys
import numpy as np
import pygame
from effects.BaseEffect import BaseEffect

# List of effect-specific requirements
REQUIREMENTS = ["Image", "Color"]

class Basic(BaseEffect):
    def __init__(self, job_id=None):
        super().__init__()
        self.label = "Quantum Blur"
        self.requirements = REQUIREMENTS
        if job_id:
            self.run_job(job_id)

    def build(self):
        # TODO: Check if everything is in the correct format
        color = pygame.Color(self.parameters["Color"])
        self.color = np.array([color.r, color.g, color.b])
        self.image = np.array(self.parameters["Image"])

    def apply(self):
        self.image[:, :] = self.color
        self.new_image = self.image

        return self.new_image


if __name__ == "__main__":

    # Ensure at least one argument is passed
    if len(sys.argv) < 2:
        print("Please provide an ID as a command-line argument.")
        sys.exit(1)

    Basic(sys.argv[1])
