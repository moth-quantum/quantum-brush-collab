import math
import random
from qiskit import QuantumCircuit, quantum_info
from qiskit.circuit.library import StatePreparation
simple_python = False
import numpy as np
from scipy.linalg import fractional_matrix_power
from PIL.Image import new as newimage, Image

def apply_mask(array, mask):
    # Validate array dimensions
    if array.ndim != 3 or array.shape[-1] != 4:
        raise ValueError("The input array must have 3 dimensions, and the last dimension must be of size 4.")

    # Validate mask dimensions
    if mask.shape != array.shape[:2]:
        raise ValueError("The mask must have the same shape as the first two dimensions of the array.")

    # Set the last value to 0 where the mask is False
    array[~mask, -1] = 0  # Modify the last value directly

    return array


def bresenham_line(x1, y1, x2, y2):
    points = []

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)

    sx = 1 if x2 > x1 else -1
    sy = 1 if y2 > y1 else -1

    if dx > dy:
        err = dx / 2.0
        while x1 != x2:
            points.append((x1, y1))
            err -= dy
            if err < 0:
                y1 += sy
                err += dx
            x1 += sx
    else:
        err = dy / 2.0
        while y1 != y2:
            points.append((x1, y1))
            err -= dx
            if err < 0:
                x1 += sx
                err += dy
            y1 += sy

    points.append((x2, y2))  # Add the last point
    return points


def interpolate_pixels(pixel_list):
    if not pixel_list:
        return []

    interpolated_pixels = [pixel_list[0]]
    # Remove consecutive duplicate pixels
    last = pixel_list[0]
    for px in pixel_list[1:]:
        if px != last:
            new_px = bresenham_line(*last,*px)
            interpolated_pixels.extend(new_px[1:])
            last = px

    return interpolated_pixels



def interpolate_points(points, num_points):
    # List to store the resulting interpolated points
    interpolated = []

    # Calculate the total number of segments between points
    total_segments = len(points) - 1

    # Total number of points to generate
    total_points = num_points

    # Generate the points
    for i in range(total_segments):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]

        # Calculate the number of points between this pair of points
        points_in_segment = total_points // total_segments
        for j in range(points_in_segment):
            t = j / points_in_segment
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t
            interpolated.append((x, y))

    # Add the last point
    interpolated.append(points[-1])

    # If we have fewer than num_points (due to division rounding), add more points
    while len(interpolated) < total_points:
        interpolated.append(points[-1])

    return interpolated


def apply_circle(mask, x, y, radius):
    # Get the shape of the mask
    width,height = mask.shape
    cx = int(x)
    cy = int(y)
    r = int(radius)
    # Loop over the bounding box around the center (cx, cy)

    for x in range(max(0, cx - r), min(width, cx + r + 1)):
        for y in range(max(0, cy - r), min(height, cy + r + 1)):
            # Check if the point (x, y) is within the circle
            if (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2:
                mask[x,y] = 1  # Set the point to 1
    return mask


def rescale_coordinates(surface_rect, coords):
    # Get the width and height of the surface
    surface_width = surface_rect.width
    surface_height = surface_rect.height

    if isinstance(coords, tuple):
        rescaled_x = max(0, min(surface_width, coords[0] - surface_rect.x))
        rescaled_y = max(0, min(surface_height, coords[1] - surface_rect.y))

        return rescaled_x, rescaled_y

    elif isinstance(coords, list):
        return [rescale_coordinates(surface_rect,crd) for crd in coords]


