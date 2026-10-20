"""Kinematics model for underwater ROV / thruster allocation."""
from typing import Dict, List
import numpy as np


class ThrusterKinematics:
    """Calculates thruster allocation from desired forces and moments."""

    def __init__(self):
        # Example 4-thruster planar / vertical configuration matrix
        # Columns: [surge, sway, heave, roll, pitch, yaw]
        self.allocation_matrix = np.array([
            [1.0,  1.0, 0.0, 0.0, 0.0,  1.0],  # Motor 1
            [1.0, -1.0, 0.0, 0.0, 0.0, -1.0],  # Motor 2
            [0.0,  0.0, 1.0, 0.0, 0.0,  0.0],  # Motor 3 (vertical)
            [0.0,  0.0, 1.0, 0.0, 0.0,  0.0],  # Motor 4 (vertical)
        ])

    def allocate(self, wrench: List[float]) -> List[float]:
        """Convert a 6-DOF wrench vector into individual thruster commands."""
        wrench_vec = np.array(wrench, dtype=float)
        thruster_outputs = np.dot(self.allocation_matrix, wrench_vec)
        # Normalize between -1.0 and 1.0
        max_val = np.max(np.abs(thruster_outputs))
        if max_val > 1.0:
            thruster_outputs /= max_val
        return thruster_outputs.tolist()
