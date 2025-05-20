#Add any dependencies but don't forget to list them in the requirements if they need to be pip installed
import numpy as np
import time  # Added proper import for sleep functionality
from qdrop_utils import *


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

    n_drops = params["user_input"]["drops"]
    assert n_drops > 1, "Number of drops must be greater than 1"

    # Split the path into n_drops smaller paths
    path_length = len(path)
    split_size = max(1, path_length // n_drops)
    split_paths = [path[i * split_size : (i + 1) * split_size] for i in range(n_drops - 1)]
    split_paths.append(path[(n_drops - 1) * split_size :])

    radius = params["user_input"]["Radius"]
    assert radius > 0, "Radius must be greater than 0"

    for lines in split_paths:
        area = points_within_radius(lines, radius)
        area = np.clip(area, [0, 0], [height - 1, width - 1])

        
        

    # other variable that you requested are available in params["user_input"]
    # the path of the stroke as well as the clicks can be found in params["stroke_input"]

    #The only thing that you need to do is to modify the image
    #image = ...

    # And return the modified image, nothing else
    return image
