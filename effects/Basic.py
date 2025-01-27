import pickle
import sys
import json
import numpy as np

def main():
    # Ensure at least one argument is passed
    if len(sys.argv) < 2:
        print("Please provide an ID as a command-line argument.")
        sys.exit(1)

    effect_id = sys.argv[1]
    with open("temp/parameters_" + effect_id + ".pkl", 'rb') as f:
        params = pickle.load(f)

    try:
        image = np.array(params["Image"])
        color = params["Color"]
        image[:,:] = np.array(color)

        with open("temp/image_"+effect_id+".pkl", 'wb') as f:
            pickle.dump(image, f)

    except json.JSONDecodeError:
        print("Invalid dictionary format. Please provide a valid JSON string.")
        sys.exit(1)


if __name__ == "__main__":
    main()