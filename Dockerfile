# Using the official Python image as a base image
FROM python:3.11

# Setting the working directory in the container
WORKDIR /App

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libparted-dev \
    libyaml-dev && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and install cython
RUN pip install --upgrade pip setuptools && \
    pip3 install cython

# Copy only the requirements file to optimize Docker caching
COPY requirements.txt .

# Install dependencies
RUN pip3 install -r requirements.txt

# Copying the FastAPI application code into the container
COPY . .

# Exposing port 80 to the outside world
EXPOSE 80

# Command to run the FastAPI application
CMD ["python3", "app.py"]

