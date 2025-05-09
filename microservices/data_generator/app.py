from flask import Flask, jsonify, request
import os
import sys
import time
import base64
import json
import logging
from datetime import datetime, timezone
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import cv2

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

SERVICE_NAME = os.environ.get('SERVICE_NAME', 'Unknown Service')
KAFKA_BROKER = os.environ.get('KAFKA_BROKER', 'localhost:9092')
DATASET_ROOT_DIR = os.environ.get('DATASET_ROOT_DIR')
CAR_TOPIC = os.environ.get('CAR_TOPIC')
PERSON_TOPIC = os.environ.get('PERSON_TOPIC')

def create_kafka_producer(bootstrap_servers, retries=10, delay=3):
    for attempt in range(retries):
        try:
            return KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        except NoBrokersAvailable:
            print(f"[Kafka] Broker not ready yet, retrying ({attempt+1}/{retries})...")
            time.sleep(delay)
    raise RuntimeError("Kafka broker not available after retries.")

producer = create_kafka_producer(KAFKA_BROKER)

def send_to_kafka(frame_id, b64_image, car_topic, person_topic, video_id):
    timestamp = datetime.now(timezone.utc).isoformat()
    message = {
        'frame_id': frame_id,
        'timestamp': timestamp,
        'video_id': video_id,
        'image': b64_image
    }
    producer.send(car_topic, message)
    producer.send(person_topic, message)
    logger.info(f"[{SERVICE_NAME}] Sent frame {frame_id}")




@app.route('/')
def hello_world():
    return f'{SERVICE_NAME} is running!'

@app.route('/status')
def status():
    status_info = {
        'service_name': SERVICE_NAME,
        'python_version': sys.version,
        'kafka_broker_env': KAFKA_BROKER,
    }
    status_info['dataset_path_configured'] = DATASET_ROOT_DIR is not None
    if DATASET_ROOT_DIR:
        status_info['dataset_path_exists'] = os.path.exists(DATASET_ROOT_DIR)
    else:
        status_info['dataset_path_exists'] = False
    return jsonify(status_info)

@app.route('/data_status')
def data_status():
    status_info = {}

    if not DATASET_ROOT_DIR:
        status_info['error'] = "DATASET_ROOT_DIR environment variable is not set."
        status_info['dataset_path'] = None
        status_info['path_exists'] = False
        status_info['contents'] = None
        status_info['expected_subdirs_found'] = False
        return jsonify(status_info), 400

    status_info['dataset_path'] = DATASET_ROOT_DIR

    path_exists = os.path.exists(DATASET_ROOT_DIR)
    status_info['path_exists'] = path_exists

    if path_exists:
        is_dir = os.path.isdir(DATASET_ROOT_DIR)
        status_info['is_directory'] = is_dir

        if is_dir:
            try:
                contents = os.listdir(DATASET_ROOT_DIR)
                status_info['contents'] = contents
                expected_subdirs = ['annotations', 'sequences']
                status_info['expected_subdirs_checked'] = expected_subdirs
                status_info['expected_subdirs_found'] = [d for d in expected_subdirs if d in contents and os.path.isdir(os.path.join(DATASET_ROOT_DIR, d))]
                status_info['all_expected_subdirs_found'] = all(d in contents and os.path.isdir(os.path.join(DATASET_ROOT_DIR, d)) for d in expected_subdirs)

                sequences_path = os.path.join(DATASET_ROOT_DIR, 'sequences')
                if os.path.isdir(sequences_path):
                    status_info['sequences_subdir_exists'] = True
                    try:
                        sequence_contents = os.listdir(sequences_path)
                        status_info['sequences_subdir_contents_count'] = len(sequence_contents)
                        status_info['sequences_subdir_contents_sample'] = sequence_contents[:5] # Show first 5
                    except Exception as e:
                        status_info['sequences_subdir_list_error'] = str(e)
                else:
                    status_info['sequences_subdir_exists'] = False

            except Exception as e:
                status_info['contents_list_error'] = str(e)
                status_info['contents'] = None
                status_info['expected_subdirs_found'] = False
                status_info['all_expected_subdirs_found'] = False
        else:
             status_info['is_directory'] = False
             status_info['contents'] = None
             status_info['expected_subdirs_found'] = False
             status_info['all_expected_subdirs_found'] = False

    else:
        status_info['contents'] = None
        status_info['is_directory'] = False
        status_info['expected_subdirs_found'] = False
        status_info['all_expected_subdirs_found'] = False


    return jsonify(status_info)


@app.route('/start/<input_id>', methods=['POST'])
def start_sequence_stream(input_id):
    input_path_seq = os.path.join(DATASET_ROOT_DIR, 'sequences', input_id)
    input_path_video = os.path.join(DATASET_ROOT_DIR, input_id)

    frame_count = 0
    CAR_TOPIC = 'car-frames'
    PERSON_TOPIC = 'person-frames'

    if os.path.isdir(input_path_seq):
        frames = sorted(f for f in os.listdir(input_path_seq) if f.lower().endswith(('.jpg', '.png')))
        for frame_file in frames:
            frame_path = os.path.join(input_path_seq, frame_file)
            with open(frame_path, 'rb') as f:
                b64_image = base64.b64encode(f.read()).decode('utf-8')
            frame_id = f'{input_id}_{frame_count}'
            send_to_kafka(frame_id, b64_image, CAR_TOPIC, PERSON_TOPIC, input_id)
            frame_count += 1
            time.sleep(0.05)
    elif os.path.isfile(input_path_video) and input_id.endswith(('.mp4', '.avi', '.mov')):
        cap = cv2.VideoCapture(input_path_video)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            _, buffer = cv2.imencode('.jpg', frame)
            b64_image = base64.b64encode(buffer.tobytes()).decode('utf-8')
            frame_id = f'{input_id.replace(".", "_")}_{frame_count:05d}'
            send_to_kafka(frame_id, b64_image, CAR_TOPIC, PERSON_TOPIC, input_id)
            frame_count += 1
            time.sleep(0.05)
        cap.release()
    else:
        return jsonify({'error': f'{input_id} is not a valid folder or video file.'}), 400

    return jsonify({'status': f'Sent {frame_count} frames from {input_id}.'})


if __name__ == '__main__':
    logger.info("Starting Flask app...")
    # import threading
    # task_thread = threading.Thread(target=run_dummy_task)
    # task_thread.daemon = True # allow main thread to exit
    # task_thread.start()
    app.run(debug=True, host='0.0.0.0', port=5000) # Listen on all interfaces
