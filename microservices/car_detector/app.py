from flask import Flask
import os
import base64
import json
import numpy as np
import cv2
import pandas as pd
from kafka import KafkaConsumer, KafkaProducer
from ultralytics import YOLO
from threading import Thread

# --- Config ---
SERVICE_NAME = os.getenv('SERVICE_NAME', 'Car Detector')
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
INPUT_TOPIC = os.getenv('INPUT_TOPIC', 'car-frames')
OUTPUT_TOPIC = os.getenv('OUTPUT_TOPIC', 'detections-cars')
YOLO_MODEL_PATH = os.getenv('YOLO_MODEL_PATH', 'yolov8n-visdrone.pt')
CSV_PATH = os.getenv('CSV_PATH', '/app/car_detections.csv')

# --- CSV Init ---
if not os.path.exists(CSV_PATH):
    pd.DataFrame(columns=[
        'frame_id', 'video_id', 'timestamp', 'label', 'confidence', 'x1', 'y1', 'x2', 'y2'
    ]).to_csv(CSV_PATH, index=False)

# --- Kafka Setup ---
consumer = KafkaConsumer(
    INPUT_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='car-detector-group'
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

model = YOLO(YOLO_MODEL_PATH)

# --- Flask ---
app = Flask(__name__)
@app.route('/')
def hello():
    return f'{SERVICE_NAME} is running!'

# --- Detection Loop ---
def detect_loop():
    print(f"[{SERVICE_NAME}] Starting detection loop...")
    for msg in consumer:
        try:
            data = msg.value
            frame_id = data.get('frame_id')
            image_b64 = data.get('image')
            image_bytes = base64.b64decode(image_b64)
            np_img = np.frombuffer(image_bytes, dtype=np.uint8)
            img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

            results = model(img)[0]
            detections = []

            for box in results.boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                if label in ['car', 'van', 'truck']:
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    detections.append({
                        'label': label,
                        'confidence': conf,
                        'bbox': [x1, y1, x2, y2]
                    })

            # Publish detections to Kafka
            payload = {
                'frame_id': frame_id,
                'video_id': data.get('video_id'),
                'timestamp': data.get('timestamp'),
                'detections': detections
            }
            producer.send(OUTPUT_TOPIC, payload)

            # Save to CSV
            if detections:
                rows = []
                for d in detections:
                    x1, y1, x2, y2 = d['bbox']
                    rows.append({
                        'frame_id': frame_id,
                        'video_id': data.get('video_id'),
                        'timestamp': data.get('timestamp'),
                        'label': d['label'],
                        'confidence': d['confidence'],
                        'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2
                    })
                pd.DataFrame(rows).to_csv(CSV_PATH, mode='a', header=False, index=False)

            print(f"[{SERVICE_NAME}] {frame_id}: {len(detections)} detections")

        except Exception as e:
            print(f"[{SERVICE_NAME}] ERROR: {e}")

# --- Main ---
if __name__ == '__main__':
    Thread(target=detect_loop, daemon=True).start()
    print(f"[{SERVICE_NAME}] Flask + Detector running...")
    app.run(host='0.0.0.0', port=5000)
