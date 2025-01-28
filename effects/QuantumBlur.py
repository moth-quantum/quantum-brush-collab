import pickle
import sys
import json
import numpy as np
import colorsys

def rgb_to_hsl(r, g, b):
    """Convert RGB (0-255) to HSL (0-1)."""
    r, g, b = r / 255, g / 255, b / 255
    return colorsys.rgb_to_hls(r, g, b)

def hsl_to_rgb(h, s, l):
    """Convert HSL (0-1) to RGB (0-255)."""
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return int(r * 255), int(g * 255), int(b * 255)

def generate_complementary_colors(rgb):
    """Generate two complementary colors from an input RGB color."""
    # Step 1: Convert RGB to HSL
    r, g, b = rgb
    h, l, s = rgb_to_hsl(r, g, b)

    # Step 2: Calculate complementary hues
    h_complement = (h + 0.5) % 1.0  # +180 degrees (0.5 in normalized hue)
    h_split1 = (h + 0.4167) % 1.0   # +150 degrees (0.4167 in normalized hue)
    h_split2 = (h + 0.5833) % 1.0   # +210 degrees (0.5833 in normalized hue)

    # Step 3: Convert HSL back to RGB
    complement_rgb = hsl_to_rgb(h_complement, s, l)
    split1_rgb = hsl_to_rgb(h_split1, s, l)
    split2_rgb = hsl_to_rgb(h_split2, s, l)

    return complement_rgb, split1_rgb, split2_rgb



def main():
    color = np.array([2, 5, 2])
    _, c1, c2 = generate_complementary_colors(tuple(color))
    c1 = np.array(c1)
    c2 = np.array(c2)

    print(np.array([color,c1,c2]).transpose())

    # Ensure at least one argument is passed
    if len(sys.argv) < 2:
        print("Please provide an ID as a command-line argument.")
        sys.exit(1)

    effect_id = sys.argv[1]
    with open("temp/parameters_" + effect_id + ".pkl", 'rb') as f:
        params = pickle.load(f)


    image = np.array(params["Image"])
    color = np.array(params["Color"])




    image[:,:] = np.array(color)

    with open("temp/image_"+effect_id+".pkl", 'wb') as f:
        pickle.dump(image, f)



if __name__ == "__main__":
    main()