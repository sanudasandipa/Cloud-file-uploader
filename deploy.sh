#!/bin/bash

# Cloud File Uploader - Docker Deployment Script

echo "🐳 Cloud File Uploader - Docker Deployment"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Run: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p uploads logs ssl

# Set permissions for uploads directory
chmod 755 uploads

# Build and start the containers
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting containers..."
docker-compose up -d

# Wait a moment for containers to start
sleep 5

# Check if containers are running
echo "🔍 Checking container status..."
docker-compose ps

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📱 Your Cloud File Uploader is now running at:"
echo "   🌐 http://localhost (with nginx)"
echo "   🐍 http://localhost:5000 (direct Flask app)"
echo ""
echo "📊 To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 To stop the application:"
echo "   docker-compose down"
echo ""
echo "🔄 To restart:"
echo "   docker-compose restart"
