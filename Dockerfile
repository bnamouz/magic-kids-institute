FROM python:3.12-slim

# System deps: ffmpeg for video composition
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg fonts-dejavu-core ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Startup: decode base64 secrets → files → run pipeline
COPY scripts/run.sh /run.sh
RUN chmod +x /run.sh

# CONTENT_TYPE (fact|song) is provided by Railway cron schedule
CMD ["/run.sh"]
