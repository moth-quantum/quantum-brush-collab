import sys
import os
import numpy as np
import mixbox
import pygame
from mixbox import rgb_to_latent, latent_to_rgb
from BaseEffect import BaseEffect
import sys
from utils import *
from qiskit.quantum_info import Statevector,Pauli

#List of effect-specific requirements
REQUIREMENTS = ["Image","Color","Strength","Orientation"]

rgb2l = lambda x: rgb_to_latent(list(x))
l2rgb = lambda x: latent_to_rgb(list(x))

def partial_x(qc, fraction):
    for j in range(qc.num_qubits):
        qc.rx(np.pi * fraction/2, j)

def measure_pauli(qc, pauli = "Z"):
    num_qubits = qc.num_qubits
    svec = Statevector(qc)

    ret = []
    for q in range(num_qubits):
        idd = ["I"] * num_qubits
        idd[q] = pauli
        ret.append(svec.expectation_value(Pauli("".join(idd))))

    return np.array(ret)

class Mixing(BaseEffect):
    def __init__(self,job_id=None):
        super().__init__()
        self.label = "Quantum Blur"
        self.requirements = REQUIREMENTS
        if job_id:
            self.run_job(job_id)

    def build(self):
        #TODO: Check if everything is in the correct format
        color = self.parameters["Color"]
        self.image = np.array(self.parameters["Image"])
        self.strength = float(self.parameters["Strength"])
        self.lcolor = np.array(mixbox.rgb_to_latent(color))
        self.latent_image = np.apply_along_axis(rgb2l, axis=-1, arr=self.image)
        self.points = self.parameters["Points"]
        self.radius = int(self.parameters["Radius"])
        self.vertical = (self.parameters["Orientation"] == "vertical")

    def circuit(self,image):
        angles = self.strength * (image - self.lcolor) * np.pi
        n_gates, n_pixels, n_qubits =  angles.shape
        n_qubits -= 3 # Remove RGB residuals
        new_image = image + 0

        for p in range(n_pixels):
            qc = QuantumCircuit(n_qubits)
            #Prepare initial state to color
            for q in range(n_qubits):
                qc.ry(self.lcolor[q] * np.pi,q)

            #Go gate by gate and get the new state
            for g in range(n_gates):
                # Apply the effect here: change the gate for something else
                for q in range(n_qubits):
                    qc.cry(angles[g,p,q],q,np.mod(q+1,n_qubits))
                    #qc.cx(q,np.mod(q+1,n_qubits))

                expect_z = np.clip(measure_pauli(qc),-1,1)[::-1]
                new_image[g,p,:n_qubits] = np.arccos(expect_z) / np.pi

        return new_image

    def apply(self):
        if self.vertical:
            cut = np.array([self.latent_image[x,y-self.radius:y+self.radius+1] for x,y in self.points])
        else:
            cut = np.array([self.latent_image[x - self.radius:x + self.radius + 1,y] for x, y in self.points])

        new_latent_image = self.latent_image + 0

        new_cut = self.circuit(cut)
        print(new_cut[:,0,:4])
        for i,val in enumerate(new_cut):
            x,y = self.points[i]
            if self.vertical:
                new_latent_image[x,y-self.radius:y+self.radius+1] = val
            else:
                new_latent_image[x - self.radius:x + self.radius + 1,y] = val

        self.new_image = np.apply_along_axis(l2rgb, axis=-1, arr=new_latent_image)

        return self.new_image

if __name__ == "__main__":
    Mixing("6104001010544694362")
    # Ensure at least one argument is passed
    if len(sys.argv) < 2:
        print("Please provide an ID as a command-line argument.")
        sys.exit(1)

    Mixing(sys.argv[1])
