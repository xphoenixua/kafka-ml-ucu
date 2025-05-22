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

## 3. Running Pipeline
You can run the pipeline, including  prcessing, detection, and tracking of cars and people on each frame of a video. Each video is broken down into frames, located in a corresponding subdirectory in `data/VisDrone2019-MOT-val/`.
To run the pipeline on a video, run this line from Docker console:
```bash
curl -X POST http://localhost:5001/start/*video_name*
```
where instead of `*video_name*` you can choose among:
- uav0000086_00000_v
- uav0000117_02622_v
- uav0000137_00458_v
- uav0000182_00000_v
- uav0000268_05773_v
- uav0000305_00000_v
- uav0000339_00001_v