import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget
from PyQt5.QtCore import QTimer
import paho.mqtt.client as mqtt
import random
import json
from mqtt_init import *  # Assuming you have MQTT setup values in this file

# MQTT Client setup
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully.")
    else:
        print("Connection failed with code:", rc)

class PaymentSystemEmulator:
    def __init__(self):
        self.client = mqtt.Client("payment_system_emulator-" + str(random.randint(1, 100000)))
        self.client.on_connect = on_connect
        self.client.username_pw_set(username, password)
        self.client.connect(broker_ip, int(broker_port))
        self.client.loop_start()
        self.topic = "parking/payment"

    def start_payment(self):
        self.client.publish(self.topic, "Payment Started")
        print("Payment started")

    def stop_payment(self):
        self.client.publish(self.topic, "Payment Stopped")
        print("Payment stopped")

    def simulate_payment(self):
        payment_amount = round(random.uniform(1, 20), 2)
        payment_status = random.choice(["success", "failed"])
        return {"amount": payment_amount, "status": payment_status}

    def publish_payment(self):
        payment_data = self.simulate_payment()
        self.client.publish(self.topic, json.dumps(payment_data))
        print(f"Published payment: {payment_data}")

class PaymentSystemGUI(QMainWindow):
    def __init__(self, emulator):
        super().__init__()
        self.emulator = emulator
        self.init_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.emulator.publish_payment)

    def init_ui(self):
        self.setWindowTitle("Payment System Emulator")
        self.setGeometry(100, 100, 300, 150)

        layout = QVBoxLayout()

        self.start_button = QPushButton("Start Payment", self)
        self.start_button.clicked.connect(self.start_payment)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Payment", self)
        self.stop_button.clicked.connect(self.stop_payment)
        layout.addWidget(self.stop_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_payment(self):
        self.emulator.start_payment()
        self.timer.start(10000)  # Publish payment every 10 seconds

    def stop_payment(self):
        self.emulator.stop_payment()
        self.timer.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    emulator = PaymentSystemEmulator()
    gui = PaymentSystemGUI(emulator)
    gui.show()

    sys.exit(app.exec_())
