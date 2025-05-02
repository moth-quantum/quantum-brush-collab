import sys
import os
import numpy as np
from qiskit.circuit.library import RXGate, RZGate,XGate,ZGate,IGate,StatePreparation
from qiskit.circuit.library import UnitaryGate
from qiskit.circuit.library import RealAmplitudes
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
 # no measurements allowed
from qiskit.quantum_info import Statevector,Pauli
from BaseEffect import BaseEffect
import sys
from utils import *

#List of effect-specific requirements
REQUIREMENTS = ["Image","Strength"]

def svd(matrix=None,U=None,S=None,Vt=None):
    if U is not None:
        S_matrix = np.diag(S)  # Convert singular values into a diagonal matrix
        mat = U @ S_matrix @ Vt
        return mat

    """Compute the Ordered Singular Value Decomposition (SVD) of a matrix."""
    U, S, Vt = np.linalg.svd(matrix, full_matrices=False)
    sorted_indices = np.argsort(S)[::-1]  # Sort singular values in descending order
    return U[:, sorted_indices], S[sorted_indices], Vt[sorted_indices, :]

def U(m,n):
    ret = IGate().to_matrix()
    if m == 1:
        ret = ret @ XGate().to_matrix()
    elif m ==-1:
        print("here")
        ret = - ret @ XGate().to_matrix()

    if n == 1 or n == -1:
        ret = ret @ ZGate().to_matrix()

    return ret

def prep(s0,s1=None): #s0 is the final state and s1 is the initial state
    if s1 is None:
        s1 = 0.5 * (np.sqrt(-3 * s0**2 + 2 * s0 + 1) - s0 + 1)
        s1 = np.clip(s1,0,1)
        #print(f"s0 {s0}")
        #print(f"s1 {s1}")
    assert s0**2 + s1**2 + s0*s1 - s0 -s1 <= 10**(-10), "Coefs must satisfy the ellipse inequality"
    return StatePreparation([np.sqrt((s0 + s1) / 2), np.sqrt((1 - s0) / 2), 0, np.sqrt((1 - s1) / 2)])


def ua_cloning(n_steps,ang, s0=2/3):
    '''
    Asymmetric universal cloning (same as the symetric case for default values)
    :param n_steps: Number of steps to repeat the cloning
    :param ang: Angle of the qubit to be cloned
    :return:
    '''
    n_qubits = 2 * n_steps - 1
    qc = QuantumCircuit(n_qubits)

    # Rotate the first qubit to encode the image
    qc.ry(ang,0)

    PG = prep(s0)
    # Creating the bell states
    for i in range(1, n_qubits, 2):
        qc.append(PG, [i, i + 1])

    ps = []
    for i in range(0, n_qubits - 1, 2):
        qc.cx(i, i + 2)
        qc.cx(i, i + 1)
        qc.cx(i + 2, i)
        qc.cx(i + 1, i)

        idd = ["I"] * n_qubits
        idd[i] = "Z"
        ps.append("".join(idd))

    idd = ["I"] * n_qubits
    idd[-1] = "Z"
    ps.append("".join(idd))

    svec = Statevector(qc)

    exp = []
    for s in ps:
        op = Pauli(s)
        exp.append(svec.expectation_value(op))

    exp = np.array(exp)

    return np.arccos(exp)

class Clone(BaseEffect):
    def __init__(self,job_id=None):
        super().__init__()
        self.label = "Cloning"
        self.requirements = REQUIREMENTS
        if job_id:
            self.run_job(job_id)

    def build(self):
        #TODO: Check if everything is in the correct format
        self.image = np.array(self.parameters["Image"])
        self.strength = float(self.parameters["Strength"])
        self.points = self.parameters["Points"]
        self.radius = int(self.parameters["Radius"])


    def apply(self):
        self.new_image = self.image + 0.
        n_points = len(self.points)

        for i in range(3):
            x0, y0 = self.points[0]
            sx = slice(x0 - self.radius, x0 + self.radius + 1)
            sy = slice(y0 - self.radius, y0 + self.radius + 1)

            copy = self.image[sx,sy,i]
            u,s,v = svd(copy)
            mls = np.mean(np.log(s))
            sls = np.std(np.log(s))

            angles = np.pi/(1+np.exp(-(np.log(s)-mls)*2/sls))

            new_angles = []
            for j,a in enumerate(angles):
                if j>=1:
                    new_angle = ua_cloning(n_points,a,self.strength)
                    new_angles.append(new_angle)
                else:
                    new_angles.append([a]*n_points)

            new_angles = np.array(new_angles)

            new_s = np.exp(mls - sls * np.log(np.pi/new_angles -1)/2)
            new_s[0] = s[0]
            for p in range(len(self.points)):
                x,y = self.points[p]
                sx = slice(x-self.radius,x+self.radius+1)
                sy = slice(y-self.radius,y+self.radius+1)

                self.new_image[sx,sy,i] = svd(U=u, S=new_s[:,p], Vt= v)

        return self.new_image

if __name__ == "__main__":

    #Clone("4092400594849537353")
    # Ensure at least one argument is passed
    if len(sys.argv) < 2:
        print("Please provide an ID as a command-line argument.")
        sys.exit(1)

    Clone(sys.argv[1])
