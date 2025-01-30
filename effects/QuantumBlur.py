import sys
import numpy as np
import mixbox
import pygame
from mixbox import rgb_to_latent, latent_to_rgb
from effects.BaseEffect import BaseEffect

#List of effect-specific requirements
REQUIREMENTS = ["Image","Color","Strength"]

rgb2l = lambda x: rgb_to_latent(list(x))
l2rgb = lambda x: latent_to_rgb(list(x))

def extract_weight(lcolor1, lcolor2):
    '''
    If we have a color2 ink, how much can we use it to create color1?
    lcolor1 = (1-t)lcolor3 + t*lcolor2
    :param color1:
    :param color2:
    :return:
    '''

    t = 1
    for i in [0,1,2]:
        for v in [-1,0,1]:
            if lcolor2[i]+v == 0:
                continue
            cond = (lcolor1[i]+v)/(lcolor2[i]+v)
            t = min(t, cond)
    t = max(t,0)

    if t ==1:
        return t

    return t


class QuantumBlur(BaseEffect):
    def __init__(self,job_id=None):
        super().__init__()
        self.label = "Quantum Blur"
        self.requirements = REQUIREMENTS
        if job_id:
            self.run_job(job_id)

    def build(self):
        #TODO: Check if everything is in the correct format
        color = pygame.Color(self.parameters["Color"])
        color = [color.r,color.g,color.b]
        self.image = np.array(self.parameters["Image"])
        self.strength = float(self.parameters["Strength"])
        self.lcolor = np.array(mixbox.rgb_to_latent(color))
        self.latent_image = np.apply_along_axis(rgb2l, axis=-1, arr=self.image)

    def apply(self):
        mix = np.array([[extract_weight(c, self.lcolor) for c in row] for row in self.latent_image])

        comp_color = np.array([[(self.latent_image[i, j] - mix[i, j] * self.lcolor) / (1 - mix[i, j]) if mix[i, j] < 1 else self.lcolor
                                for j in range(mix.shape[1])] for i in range(mix.shape[0])])


        new_mix = mix[..., np.newaxis]*self.strength

        new_latent_image = comp_color * (1 - new_mix) + new_mix * self.lcolor[np.newaxis, np.newaxis, :]

        self.new_image = np.apply_along_axis(l2rgb, axis=-1, arr=new_latent_image)

        return self.new_image

if __name__ == "__main__":

    # Ensure at least one argument is passed
    if len(sys.argv) < 2:
        print("Please provide an ID as a command-line argument.")
        sys.exit(1)

    QuantumBlur(sys.argv[1])
