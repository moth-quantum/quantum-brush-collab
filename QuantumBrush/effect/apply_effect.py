from copy import copy
import json
import importlib
import importlib.util
from pathlib import Path
import traceback
import numpy as np
from PIL import Image
import numpy as np
import sys 
import argparse
import os
import time
from utils import *

app_path = Path(sys.path[0] + "/..") # Path to the app folder

def process_variable(var_type: str, variable: any):
    match var_type:
        case "str":
            return str(variable)
        case "float":
            return float(variable)
        case "int":
            return int(variable)
        case "bool":
            if isinstance(variable, str):
                if variable.lower() in ["true", "1"]:
                    return True
                elif variable.lower() in ["false", "0"]:
                    return False
            raise ValueError("Invalid boolean format")
        case "array":
            if isinstance(variable, np.ndarray):
                return variable
            elif isinstance(variable, list):
                try:
                    return np.array(variable)
                except Exception as e:
                    raise ValueError(f"Error converting to numpy array: {e}")
            else:
                raise ValueError("Invalid array format")
        case "color":
            # Assuming color is represented as a hex string
            if isinstance(variable, str) and variable.startswith("#") and len(variable) in {7, 9}:
            # Convert hex to RGB(A) numpy array
                hex_color = variable.lstrip("#")
                if len(hex_color) == 6:  # RGB
                    return np.array([int(hex_color[i:i+2], 16) for i in (0, 2, 4)])
                elif len(hex_color) == 8:  # RGBA
                    return np.array([int(hex_color[i:i+2], 16) for i in (0, 2, 4, 6)])
                
            raise ValueError("Invalid color format")
        case _:
            raise ValueError(f"Unsupported type: {var_type}")


def process_effect(instr: dict):
    # Extract stroke_id and project_id from instructions
    stroke_id = instr.get("stroke_id", False)
    project_id = instr.get("project_id", False)

    if not stroke_id or not project_id:
        raise ValueError("stroke_id and project_id must be provided in the instructions.")
    
    project_path = app_path / f"project/{project_id}"
  
    # Get effect_id and load requirements
    effect_id = instr.get("effect_id")

    effect_path = app_path / f"effect/{effect_id}"
    req_path = effect_path / f"{effect_id}_requirements.json"

    with open(req_path, 'r') as req_file:
        req = json.load(req_file)

    # Check dependencies with version control
    for dependency, version in req.get("dependencies", {}).items():
        try:
            module = importlib.import_module(dependency)
            #TODO: Check that the version is correct
                
        except ImportError as e:
            raise ImportError(f"Failed to load dependency {dependency}: {e}")

    # Process image
    image_path = project_path / f"stroke/{stroke_id}_input.png"

    if not image_path.is_file():
        raise FileNotFoundError(f"Image file not found at {image_path}")
    
    with Image.open(image_path) as img:
        req["stroke_input"]["image_rgba"] = np.array(img.convert("RGBA")) # Ensure the image is in RGBA format


    # Process user_input and stroke_input
    for input_type in ["user_input", "stroke_input"]:
        for key in req[input_type]:
            if key == "image_rgba":
                continue # Skip image_rgba as it's already processed

            if key not in instr[input_type]:
                raise KeyError(f"Key '{key}' not found in '{input_type}' of stroke instructions.")
            
            req[input_type][key] = process_variable(req[input_type][key], instr[input_type][key])

    # Process the path and clicks

    req["stroke_input"]["path"] = req["stroke_input"]["path"][..., ::-1]
    req["stroke_input"]["clicks"] = req["stroke_input"]["clicks"][..., ::-1]

    # Process any other flags
    
    if req["flags"].get("smooth_path", False):
        req["path"] = interpolate_pixels(req["stroke_input"]["path"], numpy=True)


    # Add a few flags needed to apply the effects
    req["effect_id"] = effect_id
    req["effect_script_path"] = effect_path / f"{effect_id}.py"
    req["stroke_output_path"] = project_path / f"stroke/{stroke_id}_output.png"

    return req

def apply_effect(req: dict):
    # Save the input image to apply mask
    input_image = copy(req["stroke_input"]["image_rgba"])

    # Load and execute the effect
    spec = importlib.util.spec_from_file_location(req["effect_id"], req["effect_script_path"])
    effect_module = importlib.util.module_from_spec(spec)
    sys.modules[req["effect_id"]] = effect_module
    spec.loader.exec_module(effect_module)

    new_image = effect_module.run(req)

    # Merge the new image with the original image
    mask = np.all(new_image == input_image, axis=-1)  
    new_image[mask] = [0, 0, 0, 0]  # Set differing pixels to [0, 0, 0, 0]
    
    output_path = req["stroke_output_path"]
    output_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
    Image.fromarray(new_image.astype(np.uint8)).save(output_path, format="PNG")

    return True

def record_error(error):
    log_file = app_path / "log/error.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)  # Ensure log directory exists

    error_message = traceback.format_exc()
    
    with open(log_file, "a") as log:
        log.write(error_message)

    print(error_message)    

def dump_json(data, file_path):
    # Make sure the directory exists
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Use a safer approach for atomic file operations
    temp_path = f"{file_path}.tmp"
    try:
        with open(temp_path, "w") as f:
            json.dump(data, f)
        
        # On Windows, os.replace might fail if the destination exists
        if os.path.exists(file_path):
            os.remove(file_path)
        os.rename(temp_path, file_path)
    except Exception as e:
        # If atomic operation fails, try direct write as fallback
        print(f"Warning: Atomic write failed ({str(e)}), using direct write")
        with open(file_path, "w") as f:
            json.dump(data, f)

if __name__ == "__main__":
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Apply an effect to a stroke in a project.")
    parser.add_argument("stroke_path", type=str, help="The ID of the stroke.")
    args = parser.parse_args()

    log_file = app_path / "log/error.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)  # Ensure log directory exists

    success = False
    instructions = {}

    try:
        if not Path(args.stroke_path).is_file():
            raise FileNotFoundError(f"Stroke file not found at {args.stroke_path}")

        #Read the stroke instructions from the provided path
        with open(args.stroke_path, 'r') as stroke_file:
            instructions = json.load(stroke_file)

        instructions["effect_received"] = True
        dump_json(instructions, args.stroke_path)

        try:
            #Process the effect
            data = process_effect(instructions)

            instructions["effect_processed"] = True
            dump_json(instructions, args.stroke_path)

            #Apply the effect
            success = apply_effect(data)

            instructions["effect_success"] = success
            dump_json(instructions, args.stroke_path)

        except Exception as e:
            record_error(e)
            instructions["effect_success"] = False
            dump_json(instructions, args.stroke_path)
            success = False

    except FileNotFoundError as e:
        record_error(e)
        if instructions:
            instructions["effect_received"] = False
            dump_json(instructions, args.stroke_path)
        success = False
    except Exception as e:
        record_error(e)
        if instructions:
            instructions["effect_success"] = False
            dump_json(instructions, args.stroke_path)
        success = False

    if success:
        print("Effect applied successfully.")
        sys.exit(0)
    else:
        print("Failed to apply effect.")
        sys.exit(1)
