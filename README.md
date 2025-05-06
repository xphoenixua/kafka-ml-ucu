# kafka-ml-ucu

## 1. Dataset Setup

This project processes a dataset of images from the VisDrone Multi-Object Tracking validation dataset. The `data_generator` service will iterate through these images and send them as "frames".

Navigate to the root directory of this project in your terminal. Run the provided Python script:
    ```bash
    python download_visdrone.py
    ```
This script will download the `VisDrone2019-MOT-val.zip` archive from Google Drive and extract its contents into the `./data/VisDrone_images` directory in the project root. The `docker-compose.yaml` file is then configured to mount the `./data/VisDrone_images` directory on your host into the `/app/VisDrone_data` directory *inside* the `data_generator` container.

## 2. Docker Compose

This project uses Docker Compose to define and run the multi-container application (your microservices and Redpanda).

Navigate to the root directory of this project in your terminal (the directory containing `docker-compose.yaml`). Run the provided Docker command
    ```bash
    docker compose up --build -d
    ```

This command builds the Docker images for your microservices and then starts all the services defined in `docker-compose.yaml` in the background.

## 3. Checking Service Status

Once the Docker containers are running (`docker compose up -d`), you can check the status of individual microservices through their exposed ports and Flask endpoints.

Each microservice is configured to expose an HTTP port (mapped from the container's internal port 5000 to a specific port on the host machine).

*   **Data Generator:**  (Mapped port 5001)
    *   Access: `http://localhost:5001/`
    *   Status endpoint: `http://localhost:5001/status` - Provides general service info and confirms environment variables are set.
    *   Data check endpoint: `http://localhost:5001/data_status` - Verifies that the volume mount is working and the service can see the configured dataset directory and its contents. Check this endpoint to confirm your data is correctly mounted.

*   **Car Detector:** (Mapped port 5003)
    *   Access: `http://localhost:5003/`
    *   Status endpoint: `http://localhost:5003/status`

*   **Person Detector:** (Mapped port 5004)
    *   Access: `http://localhost:5004/`
    *   Status endpoint: `http://localhost:5004/status`

*   **Car Tracker:** (Mapped port 5005)
    *   Access: `http://localhost:5005/`
    *   Status endpoint: `http://localhost:5005/status`

*   **Person Tracker:** (Mapped port 5006)
    *   Access: `http://localhost:5006/`
    *   Status endpoint: `http://localhost:5006/status`

*   **Stats Generator:** (Mapped port 5007)
    *   Access: `http://localhost:5007/`
    *   Status endpoint: `http://localhost:5007/status`
