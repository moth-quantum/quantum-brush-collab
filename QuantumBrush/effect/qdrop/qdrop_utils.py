import numpy as np
import colorsys

def points_within_radius(points, radius):
    assert radius > 0, "Radius must be positive"
    assert isinstance(points, np.ndarray), "Points must be a numpy array"

    # Precompute offsets within the radius
    y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
    mask = x**2 + y**2 <= radius**2
    offsets = np.stack(np.nonzero(mask), axis=-1) - radius
    # Broadcast add offsets to all points
    all_points = points[:, None, :] + offsets[None, :, :]
    # Reshape and get unique points
    result = np.unique(all_points.reshape(-1, 2), axis=0)
    return result

def rgb_to_hsl(rgb):
    rgb = np.asarray(rgb, dtype=np.float32) / 255.0
    hsl = np.map(colorsys.rgb_to_hls, rgb[..., 0], rgb[..., 1], rgb[..., 2])
    
    
