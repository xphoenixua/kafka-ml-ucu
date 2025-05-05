from flask import Flask, jsonify
import os
import sys
import torch
from ultralytics import YOLO

CUDA_AVAILABLE = torch.cuda.is_available()
CUDA_INFO = {
    'device_count': torch.cuda.device_count(),
    'device_name_0': torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else None
} if CUDA_AVAILABLE else {}

app = Flask(__name__)

SERVICE_NAME = os.environ.get('SERVICE_NAME', 'Unknown Service')
KAFKA_BROKER = os.environ.get('KAFKA_BROKER', 'localhost:9092')

@app.route('/')
def hello_world():
    return f'{SERVICE_NAME} is running!'

@app.route('/status')
def status():
    return jsonify({
        'service_name': SERVICE_NAME,
        'python_version': sys.version,
        'kafka_broker_env': KAFKA_BROKER,
        'cuda_available': CUDA_AVAILABLE,
        **CUDA_INFO
    })

if __name__ == '__main__':
    print(f"[{SERVICE_NAME}] Starting Flask app on 0.0.0.0:5000...")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
