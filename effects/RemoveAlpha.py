import sys
import json
import numpy as np

def main():
    # Ensure at least one argument is passed
    if len(sys.argv) < 2:
        print("Please provide a dictionary as a command-line argument.")
        sys.exit(1)

    # Get the dictionary argument (serialized as JSON)
    dict_arg = sys.argv[1]

    try:
        # Deserialize the JSON string back into a dictionary
        received_dict = json.loads(dict_arg)
        image = np.array(received_dict["image"])
        image[:,:] = [0,0,0]
        print(json.dumps(image.tolist()))
        return json.dumps(image.tolist())

    except json.JSONDecodeError:
        print("Invalid dictionary format. Please provide a valid JSON string.")
        sys.exit(1)


if __name__ == "__main__":
    main()