FROM python:3.8-slim-buster

# Install system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

ADD src/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create a non-root user
RUN useradd -m -g operator operator
USER operator

ADD src/ /src
WORKDIR /src
CMD ["kopf", "run", "--liveness=http://0.0.0.0:8080/healthcheck", "./time_based_scaling_controller.py"]
