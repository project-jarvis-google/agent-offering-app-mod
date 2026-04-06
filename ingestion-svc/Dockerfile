# Use the official lightweight Python image.
# See https://hub.docker.com/_/python
FROM python:3.12-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Set the working directory to /app
WORKDIR /app

# Copy local code to the container image.
COPY uv.lock ./

# Install user dependencies.
RUN uv sync --frozen --no-dev

# Copy the rest of the application code
COPY . .

EXPOSE 8080

# Run the web service on container startup. Here we use the uvicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout indicated 0 is set to disable the timeouts of the workers to allow Cloud Run to handle instances scaling.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]