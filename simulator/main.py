import math
import sys
from enum import Enum

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QSlider,
    QLabel,
    QWidget,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
)
from ikpy.chain import Chain
from ikpy.link import OriginLink, URDFLink
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# Drawing constants
X_MIN = -50
X_MAX = 50
Y_MIN = -50
Y_MAX = 50
Z_MIN = -50
Z_MAX = 50
ANGLE_MIN = 0
ANGLE_MAX = 180
INITIAL_X = 30
INITIAL_Y = -10
INITIAL_Z = -10
INITIAL_HIP_ANGLE = 90
INITIAL_KNEE_ANGLE = 90
INITIAL_ANKLE_ANGLE = 90
DEBOUNCE_DELAY = 300  # ms
FIGURE_SIZE = (10, 10)
AX_LIMIT = [-50, 50]

# Physical constants
# BODY_LENGTH = 20
# BODY_WIDTH = 20

leg1 = Chain(
    name="leg1",
    links=[
        OriginLink(),
        URDFLink(
            name="hip",
            bounds=(math.radians(0), math.radians(180)),
            origin_translation=[10, -10, 0],
            origin_orientation=[0, 0, math.radians(-90)],
            rotation=[0, 0, 1],
        ),
        URDFLink(
            name="knee",
            bounds=(math.radians(0), math.radians(180)),
            origin_translation=[10, 0, 0],
            origin_orientation=[0, math.radians(180), 0],
            rotation=[0, -1, 0],
        ),
        URDFLink(
            name="ankle",
            bounds=(math.radians(0), math.radians(180)),
            origin_translation=[0, 0, 10],
            origin_orientation=[0, math.radians(-90), 0],
            rotation=[0, 1, 0],
        ),
        URDFLink(
            name="pyatka",
            origin_translation=[10, 0, 0],
            origin_orientation=[0, 0, 0],
            rotation=[1, 0, 0],
        ),
    ],
)

leg2 = Chain(
    name="leg2",
    links=[
        OriginLink(),
        URDFLink(
            name="hip",
            bounds=(math.radians(0), math.radians(180)),
            origin_translation=[-10, -10, 0],  # Mirrored x-coordinate
            origin_orientation=[0, 0, math.radians(90)],  # Mirrored z-rotation
            rotation=[0, 0, -1],  # Mirrored z-rotation axis
        ),
        URDFLink(
            name="knee",
            bounds=(math.radians(0), math.radians(180)),
            origin_translation=[-10, 0, 0],  # Mirrored x-coordinate
            origin_orientation=[0, math.radians(180), 0],
            rotation=[0, 1, 0],  # Mirrored y-rotation axis
        ),
        URDFLink(
            name="ankle",
            bounds=(math.radians(0), math.radians(180)),
            origin_translation=[0, 0, 10],
            origin_orientation=[0, math.radians(90), 0],  # Mirrored y-rotation
            rotation=[0, -1, 0],  # Mirrored y-rotation axis
        ),
        URDFLink(
            name="pyatka",
            origin_translation=[-10, 0, 0],  # Mirrored x-coordinate
            origin_orientation=[0, 0, 0],
            rotation=[-1, 0, 0],  # Mirrored x-rotation axis
        ),
    ],
)


class ChangerType(Enum):
    COORDS = 1
    ANGLES = 2


class LegUI:
    def __init__(
        self,
        name,
        chain,
        x_range,
        y_range,
        z_range,
        angle_range,
        initial_angles,
        ax,
        redraw_callback,
    ):
        self.chain = chain
        self.ax = ax
        self.redraw_callback = redraw_callback
        self.last_changer = ChangerType.COORDS
        self.ignore_sliders = False

        self.group_box = QGroupBox(f"{name} Controls")
        self.hip_slider, self.hip_label = self.create_slider_with_label(*angle_range, initial_angles[0], "Hip")
        self.knee_slider, self.knee_label = self.create_slider_with_label(*angle_range, initial_angles[1], "Knee")
        self.ankle_slider, self.ankle_label = self.create_slider_with_label(*angle_range, initial_angles[2], "Ankle")

        x, y, z = self.angles_to_pos(initial_angles[0], initial_angles[1], initial_angles[2])
        self.x_slider, self.x_label = self.create_slider_with_label(*x_range, x, "X")
        self.y_slider, self.y_label = self.create_slider_with_label(*y_range, y, "Y")
        self.z_slider, self.z_label = self.create_slider_with_label(*z_range, z, "Z")

        layout = QVBoxLayout()
        layout.addLayout(self.create_slider_layout(self.x_slider, self.x_label))
        layout.addLayout(self.create_slider_layout(self.y_slider, self.y_label))
        layout.addLayout(self.create_slider_layout(self.z_slider, self.z_label))
        layout.addLayout(self.create_slider_layout(self.hip_slider, self.hip_label))
        layout.addLayout(self.create_slider_layout(self.knee_slider, self.knee_label))
        layout.addLayout(self.create_slider_layout(self.ankle_slider, self.ankle_label))
        self.group_box.setLayout(layout)

        # Timer for debouncing
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.redraw_callback)

        # Connect sliders to debounce callback
        def on_slider_value_changed(changer):
            def inner():
                if not self.ignore_sliders:
                    self.on_slider_value_changed(changer)

            return inner

        self.x_slider.valueChanged.connect(on_slider_value_changed(ChangerType.COORDS))
        self.y_slider.valueChanged.connect(on_slider_value_changed(ChangerType.COORDS))
        self.z_slider.valueChanged.connect(on_slider_value_changed(ChangerType.COORDS))
        self.hip_slider.valueChanged.connect(on_slider_value_changed(ChangerType.ANGLES))
        self.knee_slider.valueChanged.connect(on_slider_value_changed(ChangerType.ANGLES))
        self.ankle_slider.valueChanged.connect(on_slider_value_changed(ChangerType.ANGLES))

    def create_slider_with_label(self, min_val, max_val, initial_val, label_text):
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(initial_val)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(0)
        slider.setToolTip(label_text)

        label = QLabel(f"{label_text}: {initial_val}")
        slider.valueChanged.connect(lambda value, lbl=label, lbl_text=label_text: lbl.setText(f"{lbl_text}: {value}"))

        return slider, label

    def create_slider_layout(self, slider, label):
        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(slider)
        return layout

    def on_slider_value_changed(self, changer):
        self.last_changer = changer
        if self.timer.isActive():
            self.timer.stop()
        self.timer.start(DEBOUNCE_DELAY)  # ms delay

    def update_plot(self):
        self.ignore_sliders = True
        if self.last_changer == ChangerType.COORDS:
            position = [
                self.x_slider.value(),
                self.y_slider.value(),
                self.z_slider.value(),
            ]
            ik = self.chain.inverse_kinematics(position)
            self.chain.plot(ik, self.ax, show=False)
            self.ax.scatter([position[0]], [position[1]], [position[2]], s=100)
            self.ax.set_xlim(AX_LIMIT)
            self.ax.set_ylim(AX_LIMIT)
            self.ax.set_zlim(AX_LIMIT)
            self.hip_slider.setValue(int(math.degrees(ik[1])))
            self.knee_slider.setValue(int(math.degrees(ik[2])))
            self.ankle_slider.setValue(int(math.degrees(ik[3])))
        else:
            x, y, z = self.angles_to_pos(
                self.hip_slider.value(),
                self.knee_slider.value(),
                self.ankle_slider.value(),
            )
            self.chain.plot([0, x, y, z, 0], self.ax, show=False)
            self.x_slider.setValue(int(x))
            self.y_slider.setValue(int(y))
            self.z_slider.setValue(int(z))
        self.ignore_sliders = False

    def angles_to_pos(self, hip_angle, knee_angle, ankle_angle):
        angles = [
            0,
            math.radians(hip_angle),
            math.radians(knee_angle),
            math.radians(ankle_angle),
            0,
        ]
        fk = self.chain.forward_kinematics(angles)
        x = fk[0, 3]
        y = fk[1, 3]
        z = fk[2, 3]
        return x, y, z


class IKLegGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Create the figure and canvas
        self.figure = Figure(figsize=FIGURE_SIZE)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111, projection="3d")

        # Create LegUI instances
        self.legs = [
            LegUI(
                "Leg 1",
                leg1,
                (X_MIN, X_MAX),
                (Y_MIN, Y_MAX),
                (Z_MIN, Z_MAX),
                (ANGLE_MIN, ANGLE_MAX),
                [INITIAL_HIP_ANGLE, INITIAL_KNEE_ANGLE, INITIAL_ANKLE_ANGLE],
                self.ax,
                self.update_legs,
            ),
            LegUI(
                "Leg 2",
                leg2,
                (X_MIN, X_MAX),
                (Y_MIN, Y_MAX),
                (Z_MIN, Z_MAX),
                (ANGLE_MIN, ANGLE_MAX),
                [INITIAL_HIP_ANGLE, INITIAL_KNEE_ANGLE, INITIAL_ANKLE_ANGLE],
                self.ax,
                self.update_legs,
            ),
        ]

        # Layout
        layout = QGridLayout()
        layout.addWidget(self.canvas, 0, 0, 1, 2)
        layout.addWidget(self.legs[0].group_box, 1, 0)
        layout.addWidget(self.legs[1].group_box, 1, 1)

        self.setLayout(layout)
        self.setWindowTitle("Vintik simulator GUI")

        self.update_legs()

    def update_legs(self):
        self.ax.cla()
        for leg in self.legs:
            leg.update_plot()
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = IKLegGUI()
    ex.show()
    sys.exit(app.exec_())

# TODO: float sliders
