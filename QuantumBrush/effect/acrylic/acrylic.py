import numpy as np
import time  # Added proper import for sleep functionality

def run(params):
    """
    Executes the effect pipeline based on the provided parameters.

    Args:
        parameters (dict): A dictionary containing all the relevant data.

    Returns:
        Image: the new numpy array of RGBA values or None if the effect failed
    """
    # Replace incorrect os.wait(10) with proper time.sleep(10)
    # This simulates a 10-second processing time
    time.sleep(10)
    
    # Extract image to work from
    image = params["stroke_input"]["image_rgba"]
    assert image.shape[-1] == 4, "Image must be RGBA format"

    width = image.shape[0]
    height = image.shape[1]

    # All the requirements that were requested are also available
    radius = params["user_input"]["Radius"]
    assert radius > 0, "Radius must be greater than 0"

    assert params["user_input"]["Color"].shape[0] == 3, "Color must be RGB format"
    assert params["user_input"]["Alpha"] >= 0 and params["user_input"]["Alpha"] <= 1, "Alpha must be between 0 and 1"
    
    for p in params["stroke_input"]["path"]:
        min_x = np.clip(p[1]-radius, 0, width)
        max_x = np.clip(p[1]+radius, 0, width)
        min_y = np.clip(p[0]-radius, 0, height)
        max_y = np.clip(p[0]+radius, 0, height)

        image[min_x:max_x, min_y:max_y, :3] = params["user_input"]["Color"]
        # Restore the alpha channel setting that was commented out
        image[min_x:max_x, min_y:max_y, 3] = int(params["user_input"]["Alpha"] * 255)

    return image
