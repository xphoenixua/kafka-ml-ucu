# Dockerfile for car_detector
FROM python:3.9-slim

# Install system dependencies for OpenCV and Kafka client
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
      gcc \
      libglib2.0-0 \
      libsm6 \
      libxrender1 \
      libxext6 \
      libgl1-mesa-glx \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir \
      torch==2.0.1 torchvision==0.15.2 \
      --extra-index-url https://download.pytorch.org/whl/cpu

# 2. Install ultralytics *without* its dependencies
RUN pip install --no-cache-dir ultralytics --no-deps

# 3. Install the rest of your requirements (excluding ultralytics)
RUN pip install --no-cache-dir \
      flask \
      kafka-python \
      opencv-python-headless \
      "numpy<2.0" \
      pandas \
      tqdm \
      PyYAML \
      scipy

# Copy application code
COPY app.py .

# Create directory for CSV debug output
RUN mkdir -p debug_output

# Expose Flask port
EXPOSE 5000

# Default command
CMD ["python", "app.py"]
