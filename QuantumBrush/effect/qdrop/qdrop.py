#Add any dependencies but don't forget to list them in the requirements if they need to be pip installed
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

def rgb_to_hls(rgba):
    if isinstance(rgba, list):
        rgba = np.array(rgba)
    
    if rgba.shape[-1] == 4:
         rgba = rgba[..., :3]

    if len(rgba.shape) == 1:
        hls = colorsys.rgb_to_hls(*rgba)
        return hls
    
    rgb = np.asarray(rgba, dtype=np.float32) / 255.0
    hsl = np.apply_along_axis(lambda x: colorsys.rgb_to_hsl(*x), -1, rgb)
    
    return hsl

def hls_to_rgb(hls):
    if isinstance(hls, list):
        hls = np.array(hls)
    
    if len(hls.shape) == 1:
        rgb = colorsys.hls_to_rgb(*hls)
        rgb = (rgb * 255).astype(np.uint8)
        return rgb
    
    hsl = np.asarray(hls, dtype=np.float32)
    rgb = np.apply_along_axis(lambda x: colorsys.hls_to_rgb(*x), -1, hsl)
    rgb = (rgb * 255).astype(np.uint8)
    
    return rgb
    

# The only thing that you need to change is this function
def run(params):
    """
    Executes the effect pipeline based on the provided parameters.

    Args:
        parameters (dict): A dictionary containing all the relevant data.

    Returns:
        Image: the new numpy array of RGBA values or None if the effect failed
    """

    
    # Extract image to work from
    image = params["stroke_input"]["image_rgba"]
    # It's a good practice to check any of the request variables
    assert image.shape[-1] == 4, "Image must be RGBA format"

    height = image.shape[0]
    width = image.shape[1]

    path = params["stroke_input"]["path"]

    n_drops = params["user_input"]["Number of Drops"]
    assert n_drops > 1, "Number of drops must be greater than 1"

    # Split the path into n_drops smaller paths
    path_length = len(path)
    split_size = max(1, path_length // n_drops)
    split_paths = [path[i * split_size : (i + 1) * split_size] for i in range(n_drops - 1)]
    split_paths.append(path[(n_drops - 1) * split_size :])

    radius = params["user_input"]["Radius"]
    assert radius > 0, "Radius must be greater than 0"

    target_color = params["user_input"]["Target Color"]

    for lines in split_paths:
        area = points_within_radius(lines, radius)
        area = np.clip(area, [0, 0], [height - 1, width - 1])
        area = image[area]

        hsl_area = rgb_to_hls(area)
        h,s,l = np.mean(hsl_area, axis=[0,1])
        
        ht,st,lt = rgb_to_hls(target_color)

        hsl_area[...,0] = ht
        hsl_area[...,1] = st
        hsl_area[...,2] = lt

        rgb_area = hls_to_rgb(hsl_area)

        image[area][...,:3] = rgb_area 
        
        

    # other variable that you requested are available in params["user_input"]
    # the path of the stroke as well as the clicks can be found in params["stroke_input"]

    #The only thing that you need to do is to modify the image
    #image = ...

    # And return the modified image, nothing else
    return image
