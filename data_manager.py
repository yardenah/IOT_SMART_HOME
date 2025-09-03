import paho.mqtt.client as mqtt
import json
import sqlite3
from datetime import datetime
import ssl

class DataManager:
    def __init__(self, broker_address, broker_port, db_path):
        self.client = mqtt.Client(transport="websockets")
        self.client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.client.on_message = self.on_message
        self.client.connect(broker_address, broker_port)
        self.db_conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.db_conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS parking_data
                          (timestamp TEXT, spot_id TEXT, is_occupied INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS payment_data
                          (timestamp TEXT, amount REAL, status TEXT)''')
        self.db_conn.commit()

    def on_message(self, client, userdata, message):
        topic = message.topic
        payload = json.loads(message.payload.decode())
        timestamp = datetime.now().isoformat()

        if topic.startswith("parking/spot/"):
            self.store_parking_data(timestamp, payload)
            self.check_parking_status(payload)
        elif topic == "parking/payment":
            self.store_payment_data(timestamp, payload)
            self.check_payment_status(payload)

    #save DB
    def store_parking_data(self, timestamp, data):
        cursor = self.db_conn.cursor()
        cursor.execute("INSERT INTO parking_data VALUES (?, ?, ?)",
                       (timestamp, data["spot_id"], int(data["is_occupied"])))
        self.db_conn.commit()

    def store_payment_data(self, timestamp, data):
        cursor = self.db_conn.cursor()
        cursor.execute("INSERT INTO payment_data VALUES (?, ?, ?)",
                       (timestamp, data["amount"], data["status"]))
        self.db_conn.commit()

    def check_parking_status(self, data):
        if data["is_occupied"]:
            self.send_alarm(f"Parking spot {data['spot_id']} is now occupied")
        else:
            self.send_info(f"Parking spot {data['spot_id']} is now available")

    def check_payment_status(self, data):
        if data["status"] == "failed":
            self.send_alarm(f"Payment of ${data['amount']} failed")
        else:
            self.send_info(f"Payment of ${data['amount']} successful")

    def send_alarm(self, message):
        self.client.publish("parking/alarms", json.dumps({"type": "alarm", "message": message}))

    def send_info(self, message):
        self.client.publish("parking/info", json.dumps({"type": "info", "message": message}))

    def run(self):
        self.client.subscribe("parking/#")
        self.client.loop_forever()

if __name__ == "__main__":
    data_manager = DataManager("broker.hivemq.com", 8884, "parking_system.db")
    data_manager.run()




