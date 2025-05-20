#Add any dependencies but don't forget to list them in the requirements if they need to be pip installed
import numpy as np
import time  # Added proper import for sleep functionality

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

    # other variable that you requested are available in params["user_input"]
    # the path of the stroke as well as the clicks can be found in params["stroke_input"]

    #The only thing that you need to do is to modify the image
    #image = ...

    # And return the modified image, nothing else
    return image
