from flask import Flask
import os
import time

app = Flask(__name__)

# simple endpoint to check if the service is alive
@app.route('/')
def hello_world():
    service_name = os.environ.get('SERVICE_NAME', 'Unknown Service')
    return f'{service_name} is running!'

# this is where the actual logic would go, but for the dummy app, maybe just loop or wait
def run_dummy_task():
    service_name = os.environ.get('SERVICE_NAME', 'Unknown Service')
    print(f"[{service_name}] Starting dummy task...")
    # In a real service, this would be a loop reading from/writing to Kafka
    while True:
        print(f"[{service_name}] Dummy heartbeat...")
        time.sleep(10) # Simulate work

# You might run the Flask server in one thread and the worker task in another
# Or, for a simple dummy, just run the Flask server
if __name__ == '__main__':
    # For simplicity, just run the web server.
    # Real microservices processing Kafka messages often don't need a web server,
    # or they use it only for health checks/metrics.
    # But for testing basic container startup, Flask is convenient.
    print("Starting Flask app...")
    # You might want to run the dummy task in a separate process/thread later
    # import threading
    # task_thread = threading.Thread(target=run_dummy_task)
    # task_thread.daemon = True # Allow main thread to exit
    # task_thread.start()
    app.run(debug=True, host='0.0.0.0', port=5000) # Listen on all interfaces