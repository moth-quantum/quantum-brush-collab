import sys
import os
import numpy as np
from qiskit.circuit.library import RXGate, RZGate,XGate,ZGate,IGate
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

def asym_cloning(n_steps):
    n_qubits = 2 * n_steps + 1
    qc = QuantumCircuit(n_qubits)

    #Rotate the first qubit to encode the image
    qc.x(0)

    #Creating the bell states
    for i in range(1,n_qubits,2):
        qc.h(i)
        qc.cx(i,i+1)

    w = np.array([1 / 2, 1 / 2, 1 / 2, 1 / 2]) #w00 w01 w10 w11

    w[-1] *= -1 #Need to do this to use the SparsePauliOp which does not support iY
    op = SparsePauliOp(["III", "ZZI", "XXI", "YYI"], w).to_operator()
    mat = SparsePauliOp(["III", "ZZI", "XXI", "YYI"], w).to_matrix()

    ret = [1/i for i in range(1,n_qubits+1)]
    return ret
    ps = []
    for i in range(0,n_qubits,2):
        qc.append(op, [i, i+1,i+2])

        idd = ["I"] * n_qubits
        idd[i]="Z"
        ps.append("".join(idd))

    qc.measure_all()

    simulator = AerSimulator()
    svec = simulator.run(qc, shots=1000).result().get_statevector()

    exp = []
    for op in ps:
        exp.append(svec.expectation_value(op))

    return exp

def us_cloning(n_steps):
    n_qubits = 2 * n_steps - 1
    print(n_qubits)
    qc = QuantumCircuit(n_qubits)

    #Rotate the first qubit to encode the image
    qc.x(0)

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


    for i in range(n_qubits):
        idd = ["I"] * n_qubits
        idd[i] = "Z"
        op = Pauli("".join(idd))
    print(-np.array(exp)/2 )

    return -np.array(exp)/2


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
        alphas = us_cloning(len(self.points))
        #alphas /= max(alphas)
        x0,y0 = self.points[0]
        self.new_image = self.image + 0.
        copy = self.image[x0 - self.radius:x0 + self.radius + 1, y0 - self.radius:y0 + self.radius + 1]

        for p in range(1,len(self.points)):
            x,y = self.points[p]
            sx = slice(x-self.radius,x+self.radius+1)
            sy = slice(y-self.radius,y+self.radius+1)
            paste = self.image[sx,sy]
            self.new_image[sx,sy] = alphas[p] * copy + (1-alphas[p]) * paste

        return self.new_image

if __name__ == "__main__":
    # Ensure at least one argument is passed
    if len(sys.argv) < 2:
        print("Please provide an ID as a command-line argument.")
        sys.exit(1)

    Clone(sys.argv[1])
