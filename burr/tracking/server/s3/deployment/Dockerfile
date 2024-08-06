# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies and git
RUN apt-get update && apt-get install -y \
    git \
    nginx \
    && apt-get clean

# Install the dependencies
# TODO -- use the right version
#RUN pip install "git+https://github.com/dagworks-inc/burr.git@tracker-s3#egg=burr[tracking-server-s3]"
RUN pip install "burr[tracking-server-s3]==0.26.0rc4"

# Copy the nginx config file
COPY nginx.conf /etc/nginx/nginx.conf

# Expose the port FastAPI will run on and the port NGINX will listen to
EXPOSE 8000
EXPOSE 80

ENV BURR_S3_BUCKET=burr-prod-test
ENV BURR_load_snapshot_on_start=True
ENV BURR_snapshot_interval_milliseconds=3_600_000
ENV BURR_update_interval_milliseconds=120_000
ENV BURR_BACKEND_IMPL=s3
ENV ENV DEBIAN_FRONTEND=noninteractive
ENV BURR_BACKEND_IMPL=burr.tracking.server.s3.backend.SQLiteS3Backend


# Command to run FastAPI server and NGINX
CMD ["sh", "-c", "uvicorn burr.tracking.server.run:app --host 0.0.0.0 --port 8000 & nginx -g 'daemon off;'"]
