from flask import Flask, jsonify
import os
import time
import sys

app = Flask(__name__)

SERVICE_NAME = os.environ.get('SERVICE_NAME', 'Unknown Service')
KAFKA_BROKER = os.environ.get('KAFKA_BROKER', 'localhost:9092')
DATASET_ROOT_DIR = os.environ.get('DATASET_ROOT_DIR')

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

# this is where the actual logic would go
def run_dummy_task():
    service_name = os.environ.get('SERVICE_NAME', 'Unknown Service')
    print(f"[{service_name}] Starting dummy task...")
    while True:
        print(f"[{service_name}] Dummy heartbeat...")
        time.sleep(10)

if __name__ == '__main__':
    print("Starting Flask app...")
    # import threading
    # task_thread = threading.Thread(target=run_dummy_task)
    # task_thread.daemon = True # allow main thread to exit
    # task_thread.start()
    app.run(debug=True, host='0.0.0.0', port=5000) # Listen on all interfaces
