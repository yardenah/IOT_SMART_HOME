import sys
import json
import paho.mqtt.client as mqtt
import ssl
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *



class LEDIndicatorEmulator(QObject):
    status_changed = pyqtSignal(str, bool)  # spot_id, is_occupied

    def __init__(self, broker_address, broker_port, parking_spot_id):
        super().__init__()
        self.parking_spot_id = parking_spot_id
        self.client = mqtt.Client(transport="websockets")
        self.client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.client.on_message = self.on_message
        self.client.connect(broker_address, broker_port)
        self.client.subscribe(f"parking/spot/{parking_spot_id}")
        self.is_running = False

    def on_message(self, client, userdata, message):
        payload = json.loads(message.payload.decode())
        is_occupied = payload.get("is_occupied", False)
        self.status_changed.emit(self.parking_spot_id, is_occupied)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.client.loop_start()

    def stop(self):
        if self.is_running:
            self.is_running = False
            self.client.loop_stop()


class LEDWidget(QLabel):
    def __init__(self, diameter=20):
        super().__init__()
        self.diameter = diameter
        self.setFixedSize(diameter, diameter)
        self.set_color("gray")  

    def set_color(self, color):
        pixmap = QPixmap(self.diameter, self.diameter)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(Qt.black)
        painter.drawEllipse(0, 0, self.diameter - 1, self.diameter - 1)
        painter.end()
        self.setPixmap(pixmap)


class LEDEmulatorGUI(QMainWindow):
    def __init__(self, parking_spots):
        super().__init__()
        self.emulators = {}
        self.init_ui(parking_spots)

    def init_ui(self, parking_spots):
        self.setWindowTitle("LED Emulator Controller")
        self.setGeometry(200, 200, 500, 400)

        layout = QVBoxLayout()

        for spot in parking_spots:
            group = QGroupBox(f"Parking Spot: {spot}")
            group_layout = QHBoxLayout()

            start_button = QPushButton("Start")
            stop_button = QPushButton("Stop")
            status_label = QLabel("Status: OFF")
            led_widget = LEDWidget()

            emulator = LEDIndicatorEmulator("broker.hivemq.com", 8884, spot)
            emulator.status_changed.connect(self.update_led_status)

            self.emulators[spot] = {
                "emulator": emulator,
                "status_label": status_label,
                "led_widget": led_widget
            }

            start_button.clicked.connect(lambda _, s=spot: self.start_emulator(s))
            stop_button.clicked.connect(lambda _, s=spot: self.stop_emulator(s))

            group_layout.addWidget(start_button)
            group_layout.addWidget(stop_button)
            group_layout.addWidget(status_label)
            group_layout.addWidget(led_widget)
            group.setLayout(group_layout)
            layout.addWidget(group)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_emulator(self, spot):
        emulator_data = self.emulators[spot]
        emulator = emulator_data["emulator"]
        if not emulator.is_running:
            emulator.start()
            emulator_data["status_label"].setText("Status: ON")

    def stop_emulator(self, spot):
        emulator_data = self.emulators[spot]
        emulator = emulator_data["emulator"]
        if emulator.is_running:
            emulator.stop()
            emulator_data["status_label"].setText("Status: OFF")
            emulator_data["led_widget"].set_color("gray")  

    def update_led_status(self, spot_id, is_occupied):
        emulator_data = self.emulators[spot_id]
        led_widget = emulator_data["led_widget"]
        if is_occupied:
            led_widget.set_color("red")
        else:
            led_widget.set_color("green")


if __name__ == "__main__":
    parking_spots = ["A1", "A2", "A3", "A4"]

    app = QApplication(sys.argv)
    gui = LEDEmulatorGUI(parking_spots)
    gui.show()
    sys.exit(app.exec_())
