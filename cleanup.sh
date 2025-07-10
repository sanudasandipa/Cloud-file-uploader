#!/bin/bash

# Stop and remove containers
echo "🛑 Stopping containers..."
docker-compose down

# Remove images (optional)
read -p "Do you want to remove Docker images as well? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️ Removing Docker images..."
    docker-compose down --rmi all
fi

echo "✅ Cleanup complete!"
