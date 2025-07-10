#!/bin/bash

# Test Docker deployment locally

echo "🧪 Testing Docker deployment locally..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build the image
echo "🔨 Building Docker image..."
docker build -t cloud-file-uploader-test .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

echo "✅ Docker image built successfully!"

# Run a quick test
echo "🚀 Starting test container..."
docker run -d --name cloud-uploader-test -p 5001:5000 -v $(pwd)/uploads:/app/uploads cloud-file-uploader-test

# Wait a moment for the container to start
sleep 3

# Check if container is running
if docker ps | grep cloud-uploader-test > /dev/null; then
    echo "✅ Container is running!"
    echo "🌐 Test application available at: http://localhost:5001"
    echo ""
    echo "To stop the test container:"
    echo "  docker stop cloud-uploader-test"
    echo "  docker rm cloud-uploader-test"
    echo ""
    echo "If the test works, deploy with:"
    echo "  ./deploy.sh"
else
    echo "❌ Container failed to start"
    docker logs cloud-uploader-test
    exit 1
fi
