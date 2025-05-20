import sys
import numpy as np
import pygame

from effects.BaseEffect import BaseEffect

# List of effect-specific requirements
REQUIREMENTS = ["Image", "Color"]

class Basic(BaseEffect):
    '''
    The name of the class must be the same as the name of the file!
    '''
    def __init__(self, job_id=None):
        '''
        Always initialize like thid, don't change
        :param job_id:
        '''
        super().__init__()
        self.label = "Quantum Blur"
        self.requirements = REQUIREMENTS
        if job_id:
            self.run_job(job_id)

    def build(self):
        '''
        Here we will read self.parameters and initialize the variables.
        Any used parameter here should be found in the REQUIREMENTS above
        :return:
        '''
        # TODO: Check if everything is in the correct format
        color = pygame.Color(self.parameters["Color"])
        self.color = np.array([color.r, color.g, color.b])
        self.image = np.array(self.parameters["Image"])

    def apply(self):
        '''
        In this function we will create self.new_image which wil be the updated image after the effect.
        :return: The new updated image
        '''
        self.image[:, :] = self.color
        self.new_image = self.image

        return self.new_image


if __name__ == "__main__":
    '''
    Always use this format but replace the name of the effect below
    '''
    # Ensure at least one argument is passed
    if len(sys.argv) < 2:
        print("Please provide an ID as a command-line argument.")
        sys.exit(1)

    Basic(sys.argv[1])
