#!/bin/bash

# Cloud Storage Server Startup Script

echo "🚀 Starting Cloud Storage Server..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create uploads directory
echo "📁 Creating uploads directory..."
mkdir -p uploads

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚙️ .env file not found, using default configuration..."
fi

echo "✅ Setup complete!"
echo ""
echo "🌟 Starting the server..."
echo "📡 Server will be available at: http://localhost:5000"
echo "🌍 External access: http://YOUR_SERVER_IP:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the Flask application
python app.py
