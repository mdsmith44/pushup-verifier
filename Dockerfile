FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/matplotlib
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgles2 libegl1 libglib2.0-0 libgl1 libportaudio2 && rm -rf /var/lib/apt/lists/*
COPY requirements-app.lock.txt ./
RUN pip install --no-cache-dir -r requirements-app.lock.txt
COPY pushup ./pushup
COPY config ./config
RUN useradd -m -u 10001 worker && mkdir -p /data /models && chown worker:worker /data
USER worker
ENV PUSHUP_DATA=/data PUSHUP_MODEL=/models/pose_landmarker_full.task
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "pushup.web:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
