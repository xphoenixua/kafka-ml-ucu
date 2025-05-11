import os
import json
import threading
from datetime import datetime
import pandas as pd
from flask import Flask
from kafka import KafkaConsumer

# ── Configuration ───────────────────────────────────────────────────
SERVICE_NAME      = os.getenv("SERVICE_NAME", "Stats Generator")
BROKER            = os.getenv("KAFKA_BROKER", "localhost:9092")
CAR_TOPIC         = os.getenv("CAR_TOPIC", "tracks-cars")
PEOPLE_TOPIC      = os.getenv("PEOPLE_TOPIC", "tracks-people")
CSV_PATH          = os.getenv("CSV_PATH", "/app/debug_output/stats.csv")

# ── Prepare CSV ──────────────────────────────────────────────────────
os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
if not os.path.exists(CSV_PATH):
    pd.DataFrame(columns=[
        "timestamp", "num_cars", "num_people"
    ]).to_csv(CSV_PATH, index=False)

lock         = threading.Lock()
max_car_id   = 0
max_people_id = 0

# ── Kafka Consumer ──────────────────────────────────────────────────
consumer = KafkaConsumer(
    CAR_TOPIC, PEOPLE_TOPIC,
    bootstrap_servers=BROKER,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="stats-generator-group"
)

# ── Stats Loop ──────────────────────────────────────────────────────
def stats_loop():
    global max_car_id, max_people_id
    for msg in consumer:
        data = msg.value
        tracks = data.get("tracks", [])
        # Determine which counter to update
        if msg.topic == CAR_TOPIC:
            new_max = max((t["track_id"] or 0) for t in tracks) if tracks else 0
            with lock:
                max_car_id = max(max_car_id, new_max)
        else:  # PEOPLE_TOPIC
            new_max = max((t["track_id"] or 0) for t in tracks) if tracks else 0
            with lock:
                max_people_id = max(max_people_id, new_max)

        # Append a new row with current counts
        with lock:
            row = {
                "timestamp":   datetime.utcnow().isoformat(),
                "num_cars":    max_car_id,
                "num_people":  max_people_id
            }
        pd.DataFrame([row]).to_csv(CSV_PATH, mode="a", header=False, index=False)
        print(f"[{SERVICE_NAME}] {row}")

# ── Flask Healthcheck ───────────────────────────────────────────────
app = Flask(__name__)
@app.route("/")
def health():
    return f"{SERVICE_NAME} is running!"

# ── Entrypoint ──────────────────────────────────────────────────────
if __name__ == "__main__":
    t = threading.Thread(target=stats_loop, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000)
