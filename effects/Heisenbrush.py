import sys
import os
import numpy as np
from BaseEffect import BaseEffect
import sys
from utils import *
from qiskit.quantum_info import Statevector, Pauli, SparsePauliOp
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister, generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeTorino
from qiskit_ibm_runtime import EstimatorV2 as Estimator


backend=FakeTorino()

#List of effect-specific requirements
REQUIREMENTS = ["Image","Color","Strength","Orientation"]

class Heisenbrush(BaseEffect):
    def __init__(self,job_id=None):
        super().__init__()
        self.label = "Quantum Heisenberg Effect"
        self.requirements = REQUIREMENTS
        if job_id:
            self.run_job(job_id)

    def build(self):
        #TODO: Check if everything is in the correct format
        color = self.parameters["Color"]
        self.image = np.array(self.parameters["Image"])
        self.strength = float(self.parameters["Strength"])
        # self.lcolor = np.array(mixbox.rgb_to_latent(color))
        # self.latent_image = np.apply_along_axis(rgb2l, axis=-1, arr=self.image)
        self.points = self.parameters["Points"]
        self.radius = int(self.parameters["Radius"])
        self.vertical = (self.parameters["Orientation"] == "vertical")

    def numbers_to_rgb_colors(self,numbers):
        """
        Convert a list of numbers between 0 and 1 into RGB values.
        For each number, first 2 digits after decimal become R, second 2 become G, third 2 become B.

        Args:
            numbers: List of float numbers between 0 and 1

        Returns:
            List of RGB tuples (r, g, b)
        """
        rgb_colors = []

        for num in numbers:
            # Ensure number is between 0 and 1
            num = max(0, min(1, num))

            # Remove the leading '0.' and pad with zeros to ensure at least 6 digits
            # For example, 0.567742 becomes '567742'
            digits = str(num).replace('0.', '').ljust(6, '0')

            # Extract first 2 digits for R, next 2 for G, last 2 for B
            r_str = int(digits[0:2])
            g_str = int(digits[2:4])
            b_str = int(digits[4:6])

            # Convert to integers between 0 and 255
            r = int(r_str) * 255 // 99 if r_str else 0  # Scale 00-99 to 0-255
            g = int(g_str) * 255 // 99 if g_str else 0
            b = int(b_str) * 255 // 99 if b_str else 0

            # Ensure values are in 0-255 range
            r = min(255, r)
            g = min(255, g)
            b = min(255, b)

            # Normalize to 0-1 range
            # rgb_colors.append((r/255, g/255, b/255))
            rgb_colors.append((r, g, b))

        return rgb_colors

    def create_heisenberg_hamiltonian(self,n_qubits:int, J_list: list, hz_list:list, hx_list:list):
        """
        Create a periodic boundary Heisenberg model Hamiltonian as a SparsePauliOp.

        Args:
            n_qubits (int): Number of qubits (spins) in the chain
            J_list (list): List of coupling constants for each nearest neighbor
            hz_list: local Z field for each qubit
            hx_list: local X field for each qubit

        Returns:
            SparsePauliOp: The Heisenberg Hamiltonian as a sparse Pauli operator
        """
        if not isinstance(n_qubits, int) or n_qubits < 2:
            n_qubits = 4

        if not isinstance(J_list, list) or not all(isinstance(j, (int, float)) for j in J_list):
            J_list = np.random.uniform(-1, 1, n_qubits )
        else:
            if len(J_list) != n_qubits - 1:
                raise ValueError("Length of J_list must be equal to n_qubits - 1.")

        if not isinstance(hz_list, list) or not all(isinstance(hz, (int, float)) for hz in hz_list):
            hz_list = np.random.uniform(-1, 1, n_qubits )
        else:
            if len(hz_list) != n_qubits:
                raise ValueError("Length of hz_list must be equal to n_qubits.")
        if not isinstance(hx_list, list) or not all(isinstance(hx, (int, float)) for hx in hx_list):
            hx_list = np.random.uniform(-1, 1, n_qubits )
        else:
            if len(hx_list) != n_qubits:
                raise ValueError("Length of hx_list must be equal to n_qubits.")

        pauli_strings = []
        coefficients = []

        for i in range(n_qubits - 1):
            J = J_list[i]

            for pauli in ['X', 'Y', 'Z']:
                # Create interaction between qubits i and j
                paulistr = ['I'] * n_qubits
                paulistr[i] = paulistr[i+1] = pauli
                pauli_strings.append(''.join(paulistr))
                coefficients.append(J)

        # Add periodic boundary condition
        if n_qubits > 2:
            for pauli in ['X', 'Y', 'Z']:
                paulistr = ['I'] * n_qubits
                paulistr[0] = pauli
                paulistr[n_qubits-1] = pauli
                pauli_strings.append(''.join(paulistr))
                coefficients.append(J_list[-1])

        # Add local fields X, Z
        for i in range(n_qubits):
            for pauli,hlist in zip(['X', 'Z'], [hx_list, hz_list]):
                paulistr = ['I'] * n_qubits
                paulistr[i] = pauli
                pauli_strings.append(''.join(paulistr))
                coefficients.append(hlist[i])

        # Create the SparsePauliOp
        return SparsePauliOp(pauli_strings, coefficients)


    def time_evolution_Heisenberg(self,n_qubits: int, J_list: list, hz_list:list, hx_list:list, dt:float) -> QuantumCircuit:
        """Time evolution circuit for the Heisenberg model with periodic boundary conditions
        Args:
            n_qubits: number of qubits
            J_list: interacting couplings for each nearest neighbor
            hz_list: local Z field for each qubit
            hx_list: local X field for each qubit
            dt: time step
        Returns:
            circ_dt: QuantumCircuit of the time evolution
        """
        if not isinstance(n_qubits, int) or n_qubits < 2:
            n_qubits = 4

        if not isinstance(J_list, list) or not all(isinstance(j, (int, float)) for j in J_list):
            J_list = np.random.uniform(-1, 1, n_qubits )
        else:
            if len(J_list) != n_qubits - 1:
                raise ValueError("Length of J_list must be equal to n_qubits - 1.")

        if not isinstance(hz_list, list) or not all(isinstance(hz, (int, float)) for hz in hz_list):
            hz_list = np.random.uniform(-1, 1, n_qubits )
        else:
            if len(hz_list) != n_qubits:
                raise ValueError("Length of hz_list must be equal to n_qubits.")
        if not isinstance(hx_list, list) or not all(isinstance(hx, (int, float)) for hx in hx_list):
            hx_list = np.random.uniform(-1, 1, n_qubits )
        else:
            if len(hx_list) != n_qubits:
                raise ValueError("Length of hx_list must be equal to n_qubits.")

        if not isinstance(dt, (int, float)):
            dt = 0.1
        if dt <= 0:
            raise ValueError("dt must be a positive number.")

        q = QuantumRegister(n_qubits)
        circ_dt = QuantumCircuit(q)

        for n in range(n_qubits-1):
            J = J_list[n]
            ##  exp(-it * J * (X_n X_{n+1} + Y_n Y_{n+1} + Z_n Z_{n+1}))
            circ_dt.rxx(2*J*dt, q[n], q[(n+1)%n_qubits])
            circ_dt.ryy(2*J*dt, q[n], q[(n+1)%n_qubits])
            circ_dt.rzz(2*J*dt, q[n], q[(n+1)%n_qubits])

        for n in range(n_qubits):
            ##  exp(-it * hx[n] * X_n) exp(-it * hz[n] * Z_n)
            circ_dt.rz(2*dt*hz_list[n], q[n])
            circ_dt.rx(2*dt*hx_list[n], q[n])

        return circ_dt

    def run_hardware(self,dt_list):
        # Backend
        estimator = Estimator(backend)

        nsteps = len(dt_list)
        #Hardcoding all the parameters for now
        n_qubits = 5
        J_list = [1 for _ in range(n_qubits-1)]
        hz_list = [1 for _ in range(n_qubits)]
        hx_list = [1 for _ in range(n_qubits)]

        circuits=[]
        circ = QuantumCircuit(n_qubits)
        ### start time evolution
        for step,dt in zip(range(nsteps),dt_list):
            print('step: ', step)
            circ_dt = self.time_evolution_Heisenberg(n_qubits, J_list, hz_list, hx_list, dt)
            circ = circ.compose(circ_dt)
            circuits.append(circ.copy())

        # Create the Hamiltonian
        hamiltonian = self.create_heisenberg_hamiltonian(n_qubits, J_list, hz_list, hx_list)
        observables = [hamiltonian]*len(circuits)

        # Get ISA circuits
        pm = generate_preset_pass_manager(optimization_level=2, backend=backend)
        pubs = []
        for qc, obs in zip(circuits, observables):
            isa_circuit = pm.run(qc)
            isa_obs = obs.apply_layout(isa_circuit.layout)
            pubs.append((isa_circuit, isa_obs))


        job = estimator.run(pubs)
        job_result = job.result()
        # Extract the expectation values
        values = []
        for idx in range(len(pubs)):
            pub_result = job_result[idx]
            values.append(float(pub_result.data.evs))


        values=np.abs((np.array(values)/sum(np.array(values))))

        # Normalize RGB values to [0, 1]
        return self.numbers_to_rgb_colors(values)


    def apply(self):
        #Convert the list of points into differences (and normalize them the strength)
        distances = []
        last_x,last_y = self.points[0]
        for x,y in self.points[1:]:
            distances.append( np.sqrt((x-last_x)**2 + (y-last_y)**2) )
            last_x = x
            last_y = y

        distances = self.strength * np.array(distances)/max(distances)
        #Run the algorithm to obtain the new colors
        new_colors = self.run_hardware(distances)

        #Apply the new colors directly onto the new image:
        self.new_image = self.image + 0

        inter_points = interpolate_pixels(self.points)
        color_counter = 0
        for x,y in inter_points:
            color = np.array(new_colors[color_counter])

            self.new_image[x - self.radius:x + self.radius + 1, y - self.radius:y + self.radius + 1] = color

            if (x,y) == self.points[color_counter+1]:
                color_counter +=1

        return self.new_image

if __name__ == "__main__":
    #Heisenbrush("3195284272937975157")
    # Ensure at least one argument is passed
    if len(sys.argv) < 2:
        print("Please provide an ID as a command-line argument.")
        sys.exit(1)

    Heisenbrush(sys.argv[1])