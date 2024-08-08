import math
import sys
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QSlider, QLabel, QWidget, QGridLayout, QHBoxLayout
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


class IKLegGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.leg1 = leg1
        self.initUI()

    def initUI(self):
        # Create the figure and canvas
        self.figure = Figure(figsize=FIGURE_SIZE)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111, projection='3d')



        # Create sliders for coordinates
        self.x_slider, self.x_label = self.create_slider_with_label(X_MIN, X_MAX, INITIAL_X, 'X', 0.1)
        self.y_slider, self.y_label = self.create_slider_with_label(Y_MIN, Y_MAX, INITIAL_Y, 'Y', 0.1)
        self.z_slider, self.z_label = self.create_slider_with_label(Z_MIN, Z_MAX, INITIAL_Z, 'Z', 0.1)

        # Create sliders for angles
        self.hip_angle_slider, self.hip_angle_label = self.create_slider_with_label(ANGLE_MIN, ANGLE_MAX,
                                                                                    INITIAL_HIP_ANGLE, 'Hip', 1)
        self.knee_angle_slider, self.knee_angle_label = self.create_slider_with_label(ANGLE_MIN, ANGLE_MAX,
                                                                                      INITIAL_KNEE_ANGLE, 'Knee', 1)
        self.ankle_angle_slider, self.ankle_angle_label = self.create_slider_with_label(ANGLE_MIN, ANGLE_MAX,
                                                                                        INITIAL_ANKLE_ANGLE, 'Ankle', 1)

        # Layout
        layout = QGridLayout()
        layout.addWidget(self.canvas, 0, 0, 1, 3)
        layout.addLayout(self.create_slider_layout(self.x_slider, self.x_label), 1, 0)
        layout.addLayout(self.create_slider_layout(self.y_slider, self.y_label), 1, 1)
        layout.addLayout(self.create_slider_layout(self.z_slider, self.z_label), 1, 2)
        layout.addLayout(self.create_slider_layout(self.hip_angle_slider, self.hip_angle_label), 2, 0)
        layout.addLayout(self.create_slider_layout(self.knee_angle_slider, self.knee_angle_label), 2, 1)
        layout.addLayout(self.create_slider_layout(self.ankle_angle_slider, self.ankle_angle_label), 2, 2)

        self.setLayout(layout)
        self.setWindowTitle('Vintik simulator GUI')

        # Timer for debouncing
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.update_leg)

        self.update_plot([INITIAL_X, INITIAL_Y, INITIAL_Z])

    def create_slider_with_label(self, min_val, max_val, initial_val, label_text, step):
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(initial_val)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(0)
        slider.setToolTip(label_text)

        label = QLabel(f'{label_text}: {initial_val}')
        slider.valueChanged.connect(lambda value, lbl=label, lbl_text=label_text: lbl.setText(f'{lbl_text}: {value}'))
        slider.valueChanged.connect(self.on_slider_value_changed)

        return slider, label

    def create_slider_layout(self, slider, label):
        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(slider)
        return layout

    def on_slider_value_changed(self):
        if self.timer.isActive():
            self.timer.stop()
        self.timer.start(DEBOUNCE_DELAY)  # ms delay

    def update_leg(self):
        x = self.x_slider.value()
        y = self.y_slider.value()
        z = self.z_slider.value()
        self.update_plot([x, y, z])

    def update_plot(self, position):
        ik = self.leg1.inverse_kinematics(position)
        self.ax.cla()
        self.leg1.plot(ik, self.ax, show=False)
        self.ax.scatter([position[0]], [position[1]], [position[2]], color='r', s=100)
        self.ax.set_xlim(AX_LIMIT)
        self.ax.set_ylim(AX_LIMIT)
        self.ax.set_zlim(AX_LIMIT)
        self.canvas.draw()
        self.hip_angle_slider.setValue(int(math.degrees(ik[1])))
        self.knee_angle_slider.setValue(int(math.degrees(ik[2])))
        self.ankle_angle_slider.setValue(int(math.degrees(ik[3])))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = IKLegGUI()
    ex.show()
    sys.exit(app.exec_())
