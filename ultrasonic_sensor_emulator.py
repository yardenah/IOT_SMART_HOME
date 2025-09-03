import paho.mqtt.client as mqtt
import json
import time
import random
import ssl
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys


class UltrasonicSensorEmulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.client = mqtt.Client(transport="websockets")
        self.client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.client.connect("broker.hivemq.com", 8884)
        self.running = False

    def init_ui(self):
        # Setup GUI
        self.setWindowTitle("Ultrasonic Sensor Emulator")
        self.setGeometry(100, 100, 400, 200)

        self.status_label = QLabel("Status: Stopped", self)
        self.status_label.setGeometry(20, 20, 200, 30)

        self.start_button = QPushButton("Start", self)
        self.start_button.setGeometry(20, 60, 100, 30)
        self.start_button.clicked.connect(self.start_emulation)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.setGeometry(140, 60, 100, 30)
        self.stop_button.clicked.connect(self.stop_emulation)
        self.stop_button.setEnabled(False)

        self.log_area = QTextEdit(self)
        self.log_area.setGeometry(20, 100, 360, 80)
        self.log_area.setReadOnly(True)

    def generate_data(self, parking_spot_id):
        distance = random.uniform(5, 300)
        is_occupied = distance < 100
        return {"spot_id": parking_spot_id, "distance": distance, "is_occupied": is_occupied}

    def publish_data(self):
        while self.running:
            parking_spot_id = random.choice(["A1", "A2", "A3", "A4"])
            topic = f"parking/spot/{parking_spot_id}"
            data = self.generate_data(parking_spot_id)
            self.client.publish(topic, json.dumps(data))
            log_message = f"Published to {topic}: {data}"
            print(log_message)
            self.log_area.append(log_message)
            QCoreApplication.processEvents()  # Keeps the GUI responsive
            time.sleep(5)

    def start_emulation(self):
        self.running = True
        self.status_label.setText("Status: Running")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # Start publishing data
        self.worker_thread = QThread()
        self.worker = Worker(self.publish_data)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def stop_emulation(self):
        self.running = False
        self.status_label.setText("Status: Stopped")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def closeEvent(self, event):
        self.stop_emulation()
        event.accept()


class Worker(QObject):
    finished = pyqtSignal()

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task

    def run(self):
        self.task()
        self.finished.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UltrasonicSensorEmulator()
    window.show()
    sys.exit(app.exec_())
