import pyqtgraph.opengl as gl
from PySide6.QtGui import QVector3D
import numpy as np


class OrientationWidget(gl.GLViewWidget):

    def __init__(self):
        super().__init__()

        self.setCameraPosition(distance=10, elevation=25, azimuth=45)
        self.setBackgroundColor((18, 18, 18))

        # Grid
        grid = gl.GLGridItem()
        grid.scale(2, 2, 1)
        self.addItem(grid)

        # Store drone parts
        self.parts = []

        self.build_drone()

    # ----------------------------
    # Build drone once
    # ----------------------------
    def build_drone(self):

        arm_length = 4
        arm_thickness = 0.2

        # Central body
        body = gl.GLBoxItem(size=QVector3D(1.4, 1.4, 0.3))
        body.translate(-0.7, -0.7, 0)
        self.addItem(body)
        self.parts.append(body)

        # Arms
        for angle in [45, 135, 225, 315]:
            arm = gl.GLBoxItem(size=QVector3D(arm_length, arm_thickness, 0.15))
            arm.translate(-arm_length/2, -arm_thickness/2, 0.1)
            arm.rotate(angle, 0, 0, 1)
            self.addItem(arm)
            self.parts.append(arm)

        # Motors
        for angle in [45, 135, 225, 315]:
            x = (arm_length/2) * np.cos(np.radians(angle))
            y = (arm_length/2) * np.sin(np.radians(angle))

            motor = gl.GLBoxItem(size=QVector3D(0.5, 0.5, 0.2))
            motor.translate(x - 0.25, y - 0.25, 0.2)
            self.addItem(motor)
            self.parts.append(motor)

    # ----------------------------
    # Apply rotation cleanly
    # ----------------------------
    def update_orientation(self, yaw, pitch, roll):

        for part in self.parts:
            part.resetTransform()

        # Re-apply base geometry transforms
        self.parts.clear()
        self.items = []
        self.clear()
        self.build_drone()

        for part in self.parts:
            part.rotate(yaw, 0, 0, 1)
            part.rotate(pitch, 1, 0, 0)
            part.rotate(roll, 0, 1, 0)
