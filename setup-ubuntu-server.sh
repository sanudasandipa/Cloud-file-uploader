#!/bin/bash

# Cloud File Uploader - Ubuntu Server Deployment Guide

echo "🚀 Cloud File Uploader - Ubuntu Server Deployment"
echo "=================================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Docker
install_docker() {
    echo "📦 Installing Docker..."
    
    # Update package index
    sudo apt-get update
    
    # Install prerequisites
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Set up repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    echo "✅ Docker installed successfully!"
    echo "⚠️  Please log out and log back in for group changes to take effect"
}

# Install Docker Compose (standalone)
install_docker_compose() {
    echo "📦 Installing Docker Compose..."
    
    # Download Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # Make it executable
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Create symlink
    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    echo "✅ Docker Compose installed successfully!"
}

# Main installation
main() {
    echo "🔍 Checking system requirements..."
    
    # Check if running on Ubuntu
    if ! grep -q "Ubuntu" /etc/os-release; then
        echo "⚠️  This script is designed for Ubuntu. Proceed with caution on other distributions."
    fi
    
    # Check if Docker is installed
    if ! command_exists docker; then
        install_docker
    else
        echo "✅ Docker is already installed"
    fi
    
    # Check if Docker Compose is installed
    if ! command_exists docker-compose; then
        install_docker_compose
    else
        echo "✅ Docker Compose is already installed"
    fi
    
    # Create project directory
    echo "📁 Setting up project directory..."
    mkdir -p ~/cloud-file-uploader
    cd ~/cloud-file-uploader
    
    echo ""
    echo "🎉 Installation complete!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Upload your project files to ~/cloud-file-uploader/"
    echo "2. Run: chmod +x deploy.sh"
    echo "3. Run: ./deploy.sh"
    echo ""
    echo "📁 Project will be available at: ~/cloud-file-uploader/"
    echo "🌐 Application will run on: http://your-server-ip:5000"
}

# Run main function
main
