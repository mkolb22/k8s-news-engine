FROM python:3.11-slim

WORKDIR /app
ENV PIP_NO_CACHE_DIR=1

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY worker.py ./
COPY configs ./configs

# Default: run once and exit (good for CronJob). For a long-running daemon, you could add a loop/sleep.
CMD ["python", "worker.py"]
