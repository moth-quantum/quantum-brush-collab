import sys
import os
import numpy as np
import mixbox
import pygame
from mixbox import rgb_to_latent, latent_to_rgb
from BaseEffect import BaseEffect
import sys
from utils import *

#List of effect-specific requirements
REQUIREMENTS = ["Image","Color","Strength","Orientation"]

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


def partial_x(qc, fraction):
    for j in range(qc.num_qubits):
        qc.rx(np.pi * fraction/2, j)


def get_size(height):
    """
    Determines the size of the grid for the given height map.
    """
    Lx = 0
    Ly = 0
    for (x,y) in height:
        Lx = max(x+1,Lx)
        Ly = max(y+1,Ly)
    return Lx,Ly


def array2height(array):
    height = {}
    for i,row in enumerate(array):
        for j,elem in enumerate(row):
            height[i,j] = elem
    return height

def height2array(height):
    Lx,Ly = get_size(height)
    array = np.zeros((Lx,Ly))

    for i in range(Lx):
        for j in range(Ly):
            array[i,j] = height[i,j]
    return array

class QuantumBlurFull(BaseEffect):
    def __init__(self,job_id=None):
        super().__init__()
        self.label = "Quantum Blur"
        self.requirements = REQUIREMENTS
        if job_id:
            self.run_job(job_id)

    def build(self):
        #TODO: Check if everything is in the correct format
        color = self.parameters["Color"]
        self.image = np.array(self.parameters["Image"])
        self.strength = float(self.parameters["Strength"])
        self.lcolor = np.array(mixbox.rgb_to_latent(color))
        self.latent_image = np.apply_along_axis(rgb2l, axis=-1, arr=self.image)
        self.points = self.parameters["Points"]
        self.radius = int(self.parameters["Radius"])
        self.vertical = (self.parameters["Orientation"] == "vertical")

    def apply(self):
        mix = np.array([[extract_weight(c, self.lcolor) for c in row] for row in self.latent_image])

        comp_color = np.array([[(self.latent_image[i, j] - mix[i, j] * self.lcolor) / (1 - mix[i, j]) if mix[i, j] < 1 else self.lcolor
                                for j in range(mix.shape[1])] for i in range(mix.shape[0])])
        if self.vertical:
            cut_mix = np.array([mix[x,y-self.radius:y+self.radius+1] for x,y in self.points])
        else:
            cut_mix = np.array([mix[x - self.radius:x + self.radius + 1,y] for x, y in self.points])

        max_h = np.max(cut_mix)
        qc = height2circuit(array2height(cut_mix))
        partial_x(qc, self.strength)
        new_cut_mix = height2array(circuit2height(qc))*max_h

        new_mix = mix * 1.
        for i,val in enumerate(new_cut_mix):
            x,y = self.points[i]
            if self.vertical:
                new_mix[x,y-self.radius:y+self.radius+1] = val
            else:
                new_mix[x - self.radius:x + self.radius + 1,y] = val

        new_mix=new_mix[...,np.newaxis]
        new_latent_image = comp_color * (1 - new_mix) + new_mix * self.lcolor[np.newaxis, np.newaxis, :]

        self.new_image = np.apply_along_axis(l2rgb, axis=-1, arr=new_latent_image)

        return self.new_image

if __name__ == "__main__":

    # Ensure at least one argument is passed
    if len(sys.argv) < 2:
        print("Please provide an ID as a command-line argument.")
        sys.exit(1)

    QuantumBlurFull(sys.argv[1])
