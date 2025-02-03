import sys
import numpy as np
import mixbox
import pygame
from mixbox import rgb_to_latent, latent_to_rgb
from effects.BaseEffect import BaseEffect
import sys
from utils import *

#List of effect-specific requirements
REQUIREMENTS = ["Color","Strength"]

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
        qc.rx(np.pi * fraction, j)

def partial_x(qc, fraction):
    for j in range(qc.num_qubits):
        qc.rx(np.pi * fraction, j)

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

def blur_strips(height, points, radius, strength, method='rx', rotate=False):
    """
    Applies Quantum Blur to a heighmap on a region defined by a radius
    and a set of points.

    Args:
        height (dict): a dictionary in which keys are coordinates
            for points on a grid, and the values are positive numbers
            from 0 to 1.
        points (list): a list of coordinates from the height map.
        radius (int): width (or height) of the strips formed between
            successive pairs of points, on which Quantum Blur is
            applied.
        strength (float): strength of the effect between 0 and 1.
        method (str): Type of rotation or effect to use. Should be
            `'rx'` or `'ry'`.
        rotate (bool): By default, strips have a fixed width. For
            rotate=True, they will instead have a fixed height.

    Returns:
        height (dict): A modifed height map.
    """

    L = get_size(height)
    new_height = height.copy()

    if rotate:
        for j, point in enumerate(points):
            points[j] = point[::-1]

    # radius must be rounded up to next power of 2
    radius = int(2**np.ceil(np.log2(radius)))

    origins = [] # coordinate of where the (0,0) points in the grids are in the height map
    grids = [] # grids for strips
    for j in range(len(points)-1):

        # the base point is the one with lowest y value
        if points[j][1] < points[j+1][1]:
            p0 = points[j]
            p1 = points[j+1]
        else:
            p0 = points[j+1]
            p1 = points[j]
        # origin is half the radius from base point
        origins.append((p0[0]-radius//2, p0[1]))
        if rotate:
            origins[-1] = origins[-1][::-1]

        Dx = p1[0] - p0[0] # total x offset of the strip
        h = p1[1] - p0[1] # height of the strip

        # calculate required offsets
        offset = [0]
        for y in range(1,h):
            offset.append((y*Dx)//h)

        grids.append(make_strip(offset, radius, rotate=rotate))

    for (x0,y0), (grid,n) in zip(origins, grids):
        # get the height map of the strip
        strip_height = {}
        for _, (dx, dy) in grid.items():
            # get positions in the height map (and reflect them back if they go over)
            pos = [x0 + dx, y0 + dy]
            for j, c in enumerate(pos):
                if c>=L[j]:
                    c = 2*(L[j]-1)-c
                if c<0:
                    c = abs(c)
                pos[j] = c
            strip_height[dx, dy] = new_height[tuple(pos)]
        # blur strip
        qc = height2circuit(strip_height, grid=grid, log=(method=='ry'))
        if method=='swap':
            reg = n//2
            for q in range(reg):
                qc.cx(q, q + reg)
                qc.crx(strength * np.pi, q + reg, q)
                qc.cx(q, q + reg)
        else:
            for q in range(n):
                if method=='rx':
                    qc.rx(strength*np.pi/2, q)
                elif method=='ry':
                    qc.ry(strength*np.pi/2, q)
        strip_height =circuit2height(qc, grid=grid, log=(method=='ry'))
        # update height map
        for _, (dx, dy) in grid.items():
            pos = (x0 + dx, y0 + dy)
            if pos in height:
                new_height[pos] = strip_height[dx, dy]

    return new_height


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
        self.points = self.parameters["Points"]
        self.radius = int(self.parameters["Radius"])
        self.lcolor = np.array(mixbox.rgb_to_latent(color))
        self.latent_image = np.apply_along_axis(rgb2l, axis=-1, arr=self.image)

    def apply(self):
        mix = np.array([[extract_weight(c, self.lcolor) for c in row] for row in self.latent_image])

        comp_color = np.array([[(self.latent_image[i, j] - mix[i, j] * self.lcolor) / (1 - mix[i, j]) if mix[i, j] < 1 else self.lcolor
                                for j in range(mix.shape[1])] for i in range(mix.shape[0])])

        new_mix = blur_strips(array2height(mix), self.points, self.radius, self.strength, method='rx', rotate=False)
        new_mix = height2array(new_mix)[..., np.newaxis]

        new_latent_image = comp_color * (1 - new_mix) + new_mix * self.lcolor[np.newaxis, np.newaxis, :]

        self.new_image = np.apply_along_axis(l2rgb, axis=-1, arr=new_latent_image)

        return self.new_image

if __name__ == "__main__":

    # Ensure at least one argument is passed
    if len(sys.argv) < 2:
        print("Please provide an ID as a command-line argument.")
        sys.exit(1)

    QuantumBlur(sys.argv[1])
