from qiskit.quantum_info import Statevector,Pauli
from qiskit import transpile
from BaseEffect import BaseEffect
import sys
from utils import *

#List of effect-specific requirements
REQUIREMENTS = ["Image","Strength","Color","Orientation"]

def measure_pauli(qc, pauli = "Z",method= "statevector"):
    num_qubits = qc.num_qubits
    if method == "statevector":
        svec = Statevector(qc)

        ret = []
        for q in range(num_qubits):
            idd = ["I"] * num_qubits
            idd[q] = pauli
            ret.append(svec.expectation_value(Pauli("".join(idd))))

    else:
        simulator = AerSimulator(method=method)
        qc.measure_all()
        # Run and get counts, using the matrix_product_state method
        tcirc = transpile(qc, simulator)
        result = simulator.run(tcirc).result()
        counts = result.get_counts(0)
        shots = sum(counts.values())
        if pauli == "Z":
            ret = [expectation_zzz(counts,shots,[i]) for i in range(num_qubits)]
        else:
            raise ValueError("No Pauli")

    return np.array(ret)

class Drop(BaseEffect):
    def __init__(self,job_id=None):
        super().__init__()
        self.label = "Drop"
        self.requirements = REQUIREMENTS
        if job_id:
            self.run_job(job_id)

    def build(self):
        #TODO: Check if everything is in the correct format
        self.image = np.array(self.parameters["Image"])
        self.strength = float(self.parameters["Strength"])
        self.points = self.parameters["Points"]
        self.radius = int(self.parameters["Radius"])
        self.color = self.parameters["Color"]
        self.vertical = (self.parameters["Orientation"] == "vertical")

    def apply(self):
        if self.vertical:
            cut = np.array([self.image[x, y - self.radius:y + self.radius + 1] for x, y in self.points])
        else:
            cut = np.array([self.image[x - self.radius:x + self.radius + 1, y] for x, y in self.points])

        n_qubits, n_pixels, n_channel = cut.shape

        for p in range(n_pixels):
            for c in range(n_channel):
                i_brush= np.pi * self.color[c] / 255.
                i_canvas = np.pi * cut[:,p,c] / 255.
                qc = QuantumCircuit(n_qubits + 1)
                qc.ry(i_brush,0)

                rot = self.strength * (i_brush - i_canvas)

                for q in range(1,n_qubits+1):
                    qc.ry(i_canvas[q-1], q)

                    qc.cx(0,q)
                    qc.ry(rot[q-1],0,q)
                    qc.cx(0,q)

                z_val = measure_pauli(qc,method="matrix_product_state")[1:]
                cut[:,p,c] = 254.99 * np.arccos(z_val) / np.pi


        self.new_image = self.image + 0

        for i, val in enumerate(cut):
            x, y = self.points[i]
            if self.vertical:
                self.new_image[x, y - self.radius:y + self.radius + 1] = val
            else:
                self.new_image[x - self.radius:x + self.radius + 1, y] = val

        return self.new_image

if __name__ == "__main__":
    #Drop("2887043200359254725")
    # Ensure at least one argument is passed
    if len(sys.argv) < 2:
        print("Please provide an ID as a command-line argument.")
        sys.exit(1)

    Drop(sys.argv[1])
