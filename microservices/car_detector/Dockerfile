FROM nvcr.io/nvidia/pytorch:24.05-py3

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .
