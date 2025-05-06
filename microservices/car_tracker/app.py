from flask import Flask
import os
import time

app = Flask(__name__)

# simple endpoint to check if the service is alive
@app.route('/')
def hello_world():
    service_name = os.environ.get('SERVICE_NAME', 'Unknown Service')
    return f'{service_name} is running!'

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
    