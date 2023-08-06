#!/bin/bash

# Function to build Docker image
function build_docker_image() {
    echo "Building Docker image..."
    sudo docker-compose build
    echo "Docker image $1 has been built successfully."
}

# Function to run Docker Compose
function docker_compose_up() {
    echo "Bringing up containers using Docker Compose..."
    sudo docker-compose up -d
    echo "Containers are up and running."
}

function docker_compose_down() {
    echo "Bringing down containers using Docker Compose..."
    sudo docker-compose down
   
}

# Main script starts here

# Check if the Dockerfile exists in the current directory
if [ ! -f "Dockerfile" ]; then
    echo "Error: Dockerfile not found in the current directory."
    exit 1
fi


if [ ! -f "docker-compose.yaml" ]; then
        echo "Error: docker-compose.yaml not found in the current directory."
        exit 1
fi

docker_compose_down
echo "Docker down"

# Check if the user wants to use Docker Compose
if [ "$1" = "--build" ]; then
    build_docker_image
    echo "Docker image has been built successfully."
fi

docker_compose_up
echo "Docker up and running"

