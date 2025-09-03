import tkinter as tk
from tkinter import ttk
import paho.mqtt.client as mqtt
import json
import ssl

class ParkingSystemGUI:
    def __init__(self, master):
        self.master = master
        master.title("SMART PARK System")

        self.setup_mqtt()
        self.create_widgets()

    def setup_mqtt(self):
        self.client = mqtt.Client(transport="websockets")
        self.client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.connect("broker.hivemq.com", 8884)
        self.client.subscribe("parking/#")
        self.client.loop_start()

    def create_widgets(self):
        self.parking_spots = {}
        for i in range(4):
            spot_id = f"A{i+1}"
            label = ttk.Label(self.master, text=f"Spot {spot_id}: Available")
            label.pack()
            self.parking_spots[spot_id] = label

        self.payment_label = ttk.Label(self.master, text="Last Payment: N/A")
        self.payment_label.pack()

        self.status_label = ttk.Label(self.master, text="Status: Normal")
        self.status_label.pack()

    def on_message(self, client, userdata, message):
        topic = message.topic
        try:
            payload = json.loads(message.payload.decode())
        except json.JSONDecodeError:
            print(f"Invalid JSON payload: {message.payload}")
            return

        if topic.startswith("parking/spot/"):
            spot_id = payload.get("spot_id")
            if spot_id in self.parking_spots:
                status = "Occupied" if payload.get("is_occupied") else "Available"
                self.master.after(0, self.update_spot_label, spot_id, status)
        elif topic == "parking/payment":
            amount = payload.get("amount", "N/A")
            status = payload.get("status", "N/A")
            color = "red" if payload.get("status") == "failed" else "green"
            self.master.after(0, self.update_payment_label, amount, status, color)
        elif topic in ["parking/alarms", "parking/info"]:
            message = payload.get("message", "Unknown")
            color = "red" if payload.get("type") == "alarm" else "green"
            self.master.after(0, self.update_status_label, message, color)
        else:
            print(f"Unhandled topic: {topic}")

    def on_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT broker. Attempting to reconnect...")
        try:
            client.reconnect()
        except Exception as e:
            print(f"Reconnection failed: {e}")

    def update_spot_label(self, spot_id, status):
        self.parking_spots[spot_id].config(text=f"Spot {spot_id}: {status}")

    def update_payment_label(self, amount, status, color):
        self.payment_label.config(text=f"Last Payment: ${amount} - {status}", foreground=color)

    def update_status_label(self, message, color):
        self.status_label.config(text=f"Status: {message}", foreground=color)

if __name__ == "__main__":
    root = tk.Tk()
    gui = ParkingSystemGUI(root)
    root.mainloop()
