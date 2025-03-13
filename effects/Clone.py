import sys
import os
import numpy as np
from qiskit.circuit.library import RXGate, RZGate,XGate,ZGate,IGate,StatePreparation
from qiskit.circuit.library import UnitaryGate
from qiskit.pulse import num_qubits
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

def prep(s0,s1): #s0 is the final state and s1 is the initial state
    assert s0**2 + s1**2 + s0*s1 - s0 -s1 <= 0, "Coefs but satisfy the ellipse inequality"
    return StatePreparation([np.sqrt((s0 + s1) / 2), np.sqrt((1 - s0) / 2), 0, np.sqrt((1 - s1) / 2)])


def ua_cloning(n_steps,ang):
    n_qubits = 2 * n_steps - 1
    qc = QuantumCircuit(n_qubits)

    # Rotate the first qubit to encode the image
    qc.ry(ang,0)

    PG = prep(0.9,0.1)

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

def us_cloning(n_steps,ang):
    n_qubits = 2 * n_steps - 1
    print(n_qubits)
    qc = QuantumCircuit(n_qubits)

    #Rotate the first qubit to encode the image
    qc.ry(ang,0)

    t1 = - np.arccos(np.sqrt(0.5-1/2/np.sqrt(5)))
    t2 = np.arccos((np.sqrt(5)-1)/2/np.sqrt(3))
    t3 = -np.arccos(np.sqrt(0.5-1/np.sqrt(5)))

    #Creating the bell states
    for i in range(1,n_qubits,2):
        qc.ry(-2*t1, i+1)
        qc.cx(i+1,i)
        qc.ry(-2*t2,i)
        qc.cx( i ,i+1)
        qc.ry(-2*t3,i+1)

    ps = []
    for i in range(0,n_qubits-1,2):
        qc.cx(i,i+2)
        qc.cx(i,i+1)
        qc.cx(i+2,i)
        qc.cx(i+1,i)

        idd = ["I"] * n_qubits
        idd[i]="Z"
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

        for i in range(3):
            x0, y0 = self.points[0]
            sx = slice(x0 - self.radius, x0 + self.radius + 1)
            sy = slice(y0 - self.radius, y0 + self.radius + 1)

            copy = self.image[sx,sy,i]
            u,s,v = svd(copy)
            ms = np.mean(s)
            ss = np.std(s)

            angles = np.pi/(1+np.exp(-(s-ms)/ss))
            new_angles = []
            for j,a in enumerate(angles):
                if j <3 :
                    new_angle = ua_cloning(len(self.points),a)
                    print(new_angle,a)
                    new_angles.append(new_angle)
                else:
                    new_angles.append([a]*len(self.points))

            new_angles = np.array(new_angles)

            new_s = ms - ss * np.log(np.pi/new_angles -1)

            for p in range(len(self.points)):
                x,y = self.points[p]
                sx = slice(x-self.radius,x+self.radius+1)
                sy = slice(y-self.radius,y+self.radius+1)

                self.new_image[sx,sy,i] = svd(U=u, S=new_s[:,p], Vt= v)

        return self.new_image

if __name__ == "__main__":
    # Ensure at least one argument is passed
    if len(sys.argv) < 2:
        print("Please provide an ID as a command-line argument.")
        sys.exit(1)

    Clone(sys.argv[1])
