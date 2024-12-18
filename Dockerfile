# Use an official Python runtime as a parent image
FROM python:3.12-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install available updates and python packages from requirements.txt
RUN set -ex \
    && apk upgrade --available --no-cache \
    && rm -rf /var/cache/apk/* \
    && pip install --no-cache-dir -r requirements.txt \
    && pip cache purge

# Expose port 8080
EXPOSE 8080

# Run the python app with gunicorn and bind to port 8080
CMD ["gunicorn", "-w", "2", "--error-logfile", "-", "--log-level", "debug", "-b", "0.0.0.0:8080", "app:app"]
