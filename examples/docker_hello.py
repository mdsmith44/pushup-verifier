import os
import sys

import numpy as np

print("Hello from the pushup project!")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"NumPy version: {np.__version__}")

angles = np.array([145.0, 110.0, 85.0])
print(f"Smallest elbow angle: {angles.min()} degrees")