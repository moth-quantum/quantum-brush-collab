import numpy as np

def bresenham_line(x1, y1, x2, y2):
    points = []

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)

    sx = 1 if x2 > x1 else -1
    sy = 1 if y2 > y1 else -1

    if dx > dy:
        err = dx / 2.0
        while x1 != x2:
            points.append([x1, y1])
            err -= dy
            if err < 0:
                y1 += sy
                err += dx
            x1 += sx
    else:
        err = dy / 2.0
        while y1 != y2:
            points.append([x1, y1])
            err -= dx
            if err < 0:
                x1 += sx
                err += dy
            y1 += sy

    points.append([x2, y2])  # Add the last point
    return points


def interpolate_pixels(pixel_list, numpy = True):
    if not pixel_list:
        if numpy:
            return np.array([])
        return []

    interpolated_pixels = [[pixel_list[0][0], pixel_list[0][1]]]
    # Remove consecutive duplicate pixels
    last = pixel_list[0]
    for px in pixel_list[1:]:
        if px != last:
            new_px = bresenham_line(*last,*px)
            interpolated_pixels.extend(new_px[1:])
            last = px
    if numpy:
        return np.array(interpolated_pixels)
    else:
        return interpolated_pixels



