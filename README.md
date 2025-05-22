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

## Project Description

### Intro
This project implements a distributed video stream processing pipeline, leveraging Kafka as the central asynchronous messaging system for real-time object detection and tracking. The entire setup is orchestrated via Docker Compose, which seamlessly brings up core infrastructure like Redpanda (a Kafka-compatible broker), a PostgreSQL database, and several Python-based microservices.
The Docker Compose configuration binds these microservices together. Redpanda is exposed on `9092` to the host (`localhost`) and `29092` for internal Docker network communication, with its data persisted via a `redpanda_data` volume. PostgreSQL also uses a persistent `pg_data` volume and initializes its schema via an `init.sql` script mounted to `/docker-entrypoint-initdb.d/`. All microservices are built from their respective Dockerfiles, have their code mounted into the containers, and use `depends_on` with `service_healthy` conditions to ensure they only start once Redpanda and PostgreSQL are ready.

### Ingestion
The core data flow begins with the `data_generator` service. Upon receiving an HTTP request with a video ID, this service acts as a Kafka producer. Instead of embedding large image data directly into Kafka messages, it optimizes the data pipeline by saving the raw frame bytes to a shared `frame_store` Docker volume. The path to this stored frame, along with its `frame_id`, `video_id`, and `timestamp`, is then persisted in the PostgreSQL database. This service then produces lightweight messages, serialized into JSON and encoded as UTF-8 bytes using a `value_serializer`, to two separate Kafka topics: `car-frames` and `person-frames`. The producer connects to the Redpanda broker via `bootstrap_servers` set to `redpanda:29092`, which aligns with Redpanda's `advertise-kafka-addr` configuration within the Docker network.

### Detectors
The `car_detector` and `person_detector` services are the first set of Kafka consumers. `car_detector` subscribes to the `car-frames` topic, while `person_detector` subscribes to `person-frames`. Each consumer instance is part of a `group_id` (`car-detector-group`, `person-detector-group`), allowing Kafka to distribute partitions among instances for parallel processing. 
The `auto_offset_reset='earliest'` parameter, used by our consumers, defines what happens when a consumer starts for the first time, or if its last committed offset is no longer valid (messages at that offset have expired or been deleted). 'earliest' instructs the consumer to begin reading from the very beginning of the partition (offset 0). This choice is made to ensure that all historical video frames are processed from the start of a video sequence

Upon receiving a metadata message, the `value_deserializer` decodes the JSON payload into a Python dictionary. Each service then uses the `frame_id` and `video_id` to query the PostgreSQL database for the stored image path, retrieving the actual frame bytes from the shared `frame_store` volume. 

After performing object detection using their respective YOLO models (filtering for cars/vans/trucks or pedestrians/people), they transition into Kafka producers. `car_detector` publishes its findings (a JSON payload with `frame_id`, `video_id`, `timestamp`, and a list of car `detections` including bounding boxes and confidence) to the `detections-cars` topic. Similarly, `person_detector` publishes its results to the `detections-people` topic. 

Both services utilize `enable_auto_commit=True` for automatic offset management. The `enable_auto_commit=True` parameter dictates how frequently and automatically these offsets are committed back to Kafka. When `True`, the Kafka client library periodically commits the highest offset of messages it has fetched (not necessarily fully processed) to `__consumer_offsets`. This simplifies consumer development as we don't have to manually manage commits. However, it's a trade-off: if a consumer fetches a batch of messages, auto-commits the offset for that batch, and then crashes before finishing processing all messages in that batch, those unprocessed messages might be lost (at-most-once delivery). Conversely, if it crashes after processing but before the next auto-commit, messages might be reprocessed upon restart (at-least-once delivery). For this project, the simplicity and throughput benefits of auto-commit outweigh the strict "exactly-once" processing guarantee that would require more complex manual commit logic and transactional producers.

### Trackers
Following the detection stage, `car_tracker` and `person_tracker` act as Kafka consumers, subscribing to the `detections-cars` and `detections-people` topics, respectively. They receive the detection data, deserialize it, and apply a ByteTrack algorithm to associate detections across frames, forming coherent object tracks. Once tracking is complete for a frame, they produce messages containing track IDs, updated bounding boxes, and confidence scores to `tracks-cars` and `tracks-people` Kafka topics. Like the detectors, they also append tracking results to separate CSV files for debugging and analysis.

### Output Analytics
Finally, the `stats_generator` service operates as a Kafka consumer, listening to both `tracks-cars` and `tracks-people` topics. Its purpose is to aggregate the tracking results from both streams and generate summary statistics, specifically tracking the maximum number of unique cars and people observed cumulatively across the entire video. These cumulative statistics are then written to a `stats.csv` file.
