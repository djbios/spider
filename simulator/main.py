import math
import sys
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QSlider, QLabel, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QGroupBox
from ikpy.chain import Chain
from ikpy.link import OriginLink, URDFLink
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# Constants
X_MIN = -50
X_MAX = 50
Y_MIN = -50
Y_MAX = 50
Z_MIN = -50
Z_MAX = 50
ANGLE_MIN = -180
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

leg1 = Chain(name='leg1', links=[
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
    )
])

leg2 = Chain(name='leg2', links=[
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
    )
])


class LegUI:
    def __init__(self, name, chain, x_range, y_range, z_range, angle_range, initial_pos, initial_angles, ax, debounce_callback):
        self.chain = chain
        self.ax = ax
        self.debounce_callback = debounce_callback

        self.group_box = QGroupBox(f'{name} Controls')
        self.x_slider, self.x_label = self.create_slider_with_label(*x_range, initial_pos[0], 'X')
        self.y_slider, self.y_label = self.create_slider_with_label(*y_range, initial_pos[1], 'Y')
        self.z_slider, self.z_label = self.create_slider_with_label(*z_range, initial_pos[2], 'Z')
        self.hip_slider, self.hip_label = self.create_slider_with_label(*angle_range, initial_angles[0], 'Hip')
        self.knee_slider, self.knee_label = self.create_slider_with_label(*angle_range, initial_angles[1], 'Knee')
        self.ankle_slider, self.ankle_label = self.create_slider_with_label(*angle_range, initial_angles[2], 'Ankle')

        layout = QVBoxLayout()
        layout.addLayout(self.create_slider_layout(self.x_slider, self.x_label))
        layout.addLayout(self.create_slider_layout(self.y_slider, self.y_label))
        layout.addLayout(self.create_slider_layout(self.z_slider, self.z_label))
        layout.addLayout(self.create_slider_layout(self.hip_slider, self.hip_label))
        layout.addLayout(self.create_slider_layout(self.knee_slider, self.knee_label))
        layout.addLayout(self.create_slider_layout(self.ankle_slider, self.ankle_label))
        self.group_box.setLayout(layout)

        # Connect sliders to debounce callback
        self.x_slider.valueChanged.connect(self.debounce_callback)
        self.y_slider.valueChanged.connect(self.debounce_callback)
        self.z_slider.valueChanged.connect(self.debounce_callback)
        self.hip_slider.valueChanged.connect(self.debounce_callback)
        self.knee_slider.valueChanged.connect(self.debounce_callback)
        self.ankle_slider.valueChanged.connect(self.debounce_callback)

    def create_slider_with_label(self, min_val, max_val, initial_val, label_text):
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(initial_val)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(0)
        slider.setToolTip(label_text)

        label = QLabel(f'{label_text}: {initial_val}')
        slider.valueChanged.connect(lambda value, lbl=label, lbl_text=label_text: lbl.setText(f'{lbl_text}: {value}'))

        return slider, label

    def create_slider_layout(self, slider, label):
        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(slider)
        return layout

    def update_plot(self):
        position = [self.x_slider.value(), self.y_slider.value(), self.z_slider.value()]
        ik = self.chain.inverse_kinematics(position)
        self.chain.plot(ik, self.ax, show=False)
        self.ax.scatter([position[0]], [position[1]], [position[2]], s=100)
        self.ax.set_xlim(AX_LIMIT)
        self.ax.set_ylim(AX_LIMIT)
        self.ax.set_zlim(AX_LIMIT)
        self.hip_slider.setValue(int(math.degrees(ik[1])))
        self.knee_slider.setValue(int(math.degrees(ik[2])))
        self.ankle_slider.setValue(int(math.degrees(ik[3])))


class IKLegGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Create the figure and canvas
        self.figure = Figure(figsize=FIGURE_SIZE)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111, projection='3d')

        # Create LegUI instances
        self.legs = [
            LegUI('Leg 1', leg1, (X_MIN, X_MAX), (Y_MIN, Y_MAX), (Z_MIN, Z_MAX), (ANGLE_MIN, ANGLE_MAX),
                  [INITIAL_X, INITIAL_Y, INITIAL_Z], [INITIAL_HIP_ANGLE, INITIAL_KNEE_ANGLE, INITIAL_ANKLE_ANGLE],
                  self.ax, self.on_slider_value_changed),
            LegUI('Leg 2', leg2, (X_MIN, X_MAX), (Y_MIN, Y_MAX), (Z_MIN, Z_MAX), (ANGLE_MIN, ANGLE_MAX),
                  [INITIAL_X, INITIAL_Y, INITIAL_Z], [INITIAL_HIP_ANGLE, INITIAL_KNEE_ANGLE, INITIAL_ANKLE_ANGLE],
                  self.ax, self.on_slider_value_changed)
        ]

        # Layout
        layout = QGridLayout()
        layout.addWidget(self.canvas, 0, 0, 1, 2)
        layout.addWidget(self.legs[0].group_box, 1, 0)
        layout.addWidget(self.legs[1].group_box, 1, 1)

        self.setLayout(layout)
        self.setWindowTitle('Vintik simulator GUI')

        # Timer for debouncing
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.update_legs)

        self.update_legs()

    def on_slider_value_changed(self):
        if self.timer.isActive():
            self.timer.stop()
        self.timer.start(DEBOUNCE_DELAY)  # ms delay

    def update_legs(self):
        self.ax.cla()
        for leg in self.legs:
            leg.update_plot()
        self.canvas.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = IKLegGUI()
    ex.show()
    sys.exit(app.exec_())
