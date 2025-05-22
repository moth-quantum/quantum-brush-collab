#Add any dependencies but don't forget to list them in the requirements if they need to be pip installed
import numpy as np
import colorsys
from qiskit import QuantumCircuit
from qiskit.quantum_info import Pauli, SparsePauliOp, Statevector
import math
def points_within_radius(points, radius):
    """
    Given a set of points and a radius, return all points within the radius.
    Args:
        points (np.ndarray): Array of shape (N, 2) where N is the number of points.
        radius (int): The radius to search within.
    Returns:
        np.ndarray: Array of points within the radius.
    """


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

def rgb_to_hls(rgba: np.ndarray):
    """
    Convert an RGB array to HLS format.
    If the input is RGBA, the alpha channel is preserved.
    Args:
        rgba (np.ndarray): Input array of shape (N, 4) or (N, 3).
    Returns:
        np.ndarray: Converted array in HLS format.
    """

    if rgba.shape[-1] == 4:
        rgb = rgba[..., :3]

        if len(rgb.shape) == 1:
            hls = colorsys.rgb_to_hls(*rgb)
            hls.append(rgba[3])

        else:
            hls = np.apply_along_axis(lambda x: colorsys.rgb_to_hls(*x), -1, rgb)
            hls = np.concatenate([hls, rgba[..., 3][..., np.newaxis]], axis=-1)
    
    else:
        rgb = rgba

        if len(rgb.shape) == 1:
            hls = colorsys.rgb_to_hls(*rgb)

        else:
            hls = np.apply_along_axis(lambda x: colorsys.rgb_to_hls(*x), -1, rgb)

    return hls
    
def hls_to_rgb(hlsa: np.ndarray):

    if hlsa.shape[-1] == 4:
        hls = hlsa[..., :3]

        if len(hls.shape) == 1:
            rgb = colorsys.hls_to_rgb(*hls)
            rgb.append(hlsa[3])

        else:
            rgb = np.apply_along_axis(lambda x: colorsys.hls_to_rgb(*x), -1, hls)
            rgb = np.concatenate([rgb, hlsa[..., 3][..., np.newaxis]], axis=-1)
    
    else:
        hls = hlsa

        if len(hls.shape) == 1:
            rgb = colorsys.hls_to_rgb(*hls)

        else:
            rgb = np.apply_along_axis(lambda x: colorsys.hls_to_rgb(*x), -1, hls)

    return rgb


def dephasing(initial_angles, target_angles, strength):
    num_qubits = len(initial_angles)

    # We ned first to align the target angle to to z axis

    qc = QuantumCircuit(num_qubits + 1)
    rotation = 2*np.arccos(1-strength)

    # Prepare each qubit in the state defined by (theta, phi)
    for i, (theta, phi) in enumerate(initial_angles):
        qc.ry(theta, i)
        qc.rz(phi, i)

        qc.cry(rotation,target_qubit = num_qubits,control_qubit  = i)
        qc.cx(target_qubit = i,control_qubit  = num_qubits)

    qc.reset(qubit = num_qubits)

    # Get statevector for expectation value calculation
    sv = Statevector.from_instruction(qc)

    # Define Pauli operators for X and Z for each qubit
    x_ops = [SparsePauliOp(Pauli('I'*(num_qubits-i) + 'X' + 'I'*i)) for i in range(num_qubits)]
    y_ops = [SparsePauliOp(Pauli('I'*(num_qubits-i) + 'Y' + 'I'*i)) for i in range(num_qubits)]
    z_ops = [SparsePauliOp(Pauli('I'*(num_qubits-i) + 'Z' + 'I'*i)) for i in range(num_qubits)]

    # Calculate expectation values
    x_expectations = [sv.expectation_value(op).real for op in x_ops]
    y_expectations = [sv.expectation_value(op).real for op in y_ops]
    z_expectations = [sv.expectation_value(op).real for op in z_ops]

    # theta = arccos(Z)
    theta_expectations = [np.arccos(np.clip(z, -1.0, 1.0)) for z in z_expectations]
    # phi = arctan2(Y, X)
    phi_expectations = [np.arctan2(y, x) for x, y in zip(x_expectations, y_expectations)]

    final_angles = list(zip(theta_expectations, phi_expectations))
    print("final angles",final_angles)
    return final_angles







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

    # Split a path into n_drops smaller paths
    path_length = len(path)
    assert path_length > n_drops, "The number of pixels in the stroke must be bigger than the number of drops"

    split_size = max(1, path_length // n_drops)
    split_paths = [path[i * split_size : (i + 1) * split_size] for i in range(n_drops - 1)]
    split_paths.append(path[(n_drops - 1) * split_size :])

    # Get the radius of the drop
    radius = params["user_input"]["Radius"]
    assert radius > 0, "Radius must be greater than 0"

    target_hls = rgb_to_hls(params["user_input"]["Target Color"])
    target_angles = (2 * np.pi * target_hls[1], target_hls[0] * np.pi)  

    initial_angles = [] #(Theta,phi)
    pixels = []
    for lines in split_paths:

        region = points_within_radius(lines, radius)
        region = np.clip(region, [0, 0], [height - 1, width - 1])

        selection = image[region[:, 0], region[:, 1]]
        selection = selection.astype(np.float32) / 255.0
        selection_hls = rgb_to_hls(selection)

    
        h_sel = np.mean(selection_hls[..., 0], axis=0)
        l_sel = np.mean(selection_hls[..., 1], axis=0)
        theta = np.pi * (1-l_sel)
        phi = 2 * np.pi * h_sel

        initial_angles.append((theta, phi))
        pixels.append((region, selection_hls))

    strength = params["user_input"]["Strength"]
    assert strength >= 0 and strength <= 1, "Strength must be between 0 and 1"

    final_angles =  dephasing(initial_angles, target_angles, strength)

    for i,(region,selection_hls) in enumerate(pixels):
        new_h,new_l = final_angles[i]
        old_h, old_l = initial_angles[i]

        selection_hls[...,0] += (new_h - old_h) / (2 * np.pi)
        selection_hls[...,1] += (new_l - old_l) / np.pi
        selection_hls[...,1] = 1- selection_hls[...,1]
        #Need to change the luminoisty
        selection_hls = np.clip(selection_hls, 0, 1)

        selection_rgb = hls_to_rgb(selection_hls)
        selection_rgb = (selection_rgb * 254).astype(np.uint8)

        image[region[:, 0], region[:, 1]] = selection_rgb
        
        
    return image
