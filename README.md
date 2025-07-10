# 🌟 Cloud File Storage - Docker Edition

A modern, responsive web application for cloud file storage built with Python Flask backend and vanilla JavaScript frontend. Now with Docker support for easy deployment on Ubuntu servers!

## ✨ Features

- **📤 File Upload**: Drag & drop or click to upload multiple files (up to 3GB)
- **📥 File Download**: Direct download of stored files
- **🗑️ File Management**: Delete files with confirmation modal
- **📊 Storage Info**: Real-time storage usage statistics
- **📱 Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **🎨 Modern UI**: Beautiful gradient design with smooth animations
- **🚀 Fast Performance**: Optimized for quick file operations
- **🔒 Secure**: Filename sanitization and file type validation
- **🐳 Docker Ready**: Easy deployment with Docker containers
- **🌐 Production Ready**: Nginx reverse proxy included

## 🛠️ Technical Stack

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Deployment**: Docker & Docker Compose
- **Reverse Proxy**: Nginx (optional)
- **Storage**: Persistent Docker volumes

## 📋 Prerequisites

- Ubuntu Server (20.04+ recommended)
- 2GB+ RAM
- 50GB+ available storage
- Internet connection for Docker installation

## 🚀 Quick Deployment Guide

### Option 1: Automated Setup (Recommended)

1. **Clone/Upload the project to your Ubuntu server**
2. **Run the automated setup**:
   ```bash
   chmod +x setup-ubuntu-server.sh deploy.sh
   ./setup-ubuntu-server.sh
   ./deploy.sh
   ```

### Option 2: Manual Docker Setup

1. **Install Docker on Ubuntu**:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   # Log out and log back in
   ```

2. **Install Docker Compose**:
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **Deploy the application**:
   ```bash
   docker-compose up -d
   ```

### Access Your Application

- **Direct Flask App**: `http://your-server-ip:5000`
- **With Nginx** (full setup): `http://your-server-ip`

## 📁 Project Structure

```
Cloud-file-uploader/
├── app.py                 # Flask backend application
├── requirements.txt       # Python dependencies
├── start.sh              # Startup script
├── .env                  # Environment configuration
├── .gitignore           # Git ignore rules
├── templates/
│   └── index.html       # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css    # Responsive CSS styles
│   └── js/
│       └── app.js       # Frontend JavaScript
└── uploads/             # File storage directory (created automatically)
```

## ⚙️ Configuration

### Environment Variables (.env)
```bash
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=True
MAX_FILE_SIZE=104857600  # 100MB in bytes
UPLOAD_FOLDER=uploads
```

### Server Configuration (app.py)
- **Upload folder**: `uploads/`
- **Max file size**: 100MB per file
- **Host**: `0.0.0.0` (accessible from network)
- **Port**: `5000`

## 🔧 Manual Setup (Alternative)

If you prefer manual setup:

### 1. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Create Upload Directory
```bash
mkdir -p uploads
```

### 4. Run the Application
```bash
python app.py
```

## 🌐 Network Access Setup

To access your cloud storage from other devices on your network:

### 1. Find Your Server IP
```bash
ip addr show
# or
hostname -I
```

### 2. Configure Firewall (if needed)
```bash
sudo ufw allow 5000
```

### 3. Access from Network
Use `http://YOUR_SERVER_IP:5000` from any device on your network.

## 🔒 Security Considerations

### For Production Use:
1. **Use HTTPS**: Set up SSL/TLS certificates
2. **Authentication**: Add user login system
3. **File Validation**: Implement stricter file type checking
4. **Rate Limiting**: Prevent abuse
5. **Reverse Proxy**: Use Nginx or Apache
6. **Environment**: Set `FLASK_ENV=production`

### Basic Security Features Included:
- Filename sanitization
- File size limits
- CORS protection
- Path traversal prevention

## 📱 Browser Compatibility

- ✅ Chrome 60+
- ✅ Firefox 55+
- ✅ Safari 12+
- ✅ Edge 79+
- ✅ Mobile browsers

## 🎯 API Endpoints

### File Operations
- `GET /api/files` - List all files
- `POST /api/upload` - Upload file(s)
- `GET /api/download/<filename>` - Download file
- `DELETE /api/delete/<filename>` - Delete file
- `GET /api/storage` - Get storage information

### Response Format
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "files": [...],
  "storage": {...}
}
```

## 🐛 Troubleshooting

### Common Issues

**Port 5000 already in use:**
```bash
sudo lsof -t -i tcp:5000 | xargs kill -9
```

**Permission denied on uploads folder:**
```bash
sudo chown -R $USER:$USER uploads/
chmod 755 uploads/
```

**Module not found errors:**
```bash
pip install -r requirements.txt
```

**Can't access from network:**
- Check firewall settings
- Verify server IP address
- Ensure Flask runs on 0.0.0.0

## 🔄 Updates and Maintenance

### Update Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Monitor Storage Usage
```bash
df -h
du -sh uploads/
```

### Backup Files
```bash
tar -czf backup-$(date +%Y%m%d).tar.gz uploads/
```

## 🐳 Docker Management

### Container Operations
```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f

# Stop the application
docker-compose down

# Restart the application
docker-compose restart

# Rebuild and start
docker-compose up --build -d
```

### Alternative Deployment Options

#### Simple Flask-only deployment:
```bash
docker-compose -f docker-compose.simple.yml up -d
```

#### With custom environment:
```bash
# Create .env file with custom settings
echo "MAX_FILE_SIZE=5368709120" > .env  # 5GB limit
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file for custom settings:
```env
FLASK_ENV=production
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=3221225472  # 3GB in bytes
```

### Firewall Setup
```bash
# Allow HTTP traffic
sudo ufw allow 80

# Allow HTTPS traffic  
sudo ufw allow 443

# Allow direct Flask access (optional)
sudo ufw allow 5000
```

## 🚨 Troubleshooting

### Common Issues

1. **Permission Denied**:
   ```bash
   sudo chown -R $USER:$USER uploads/
   chmod 755 uploads/
   ```

2. **Port Already in Use**:
   ```bash
   sudo netstat -tulpn | grep :5000
   docker-compose down  # Stop existing containers
   ```

3. **Docker Permission Issues**:
   ```bash
   sudo usermod -aG docker $USER
   # Log out and log back in
   ```

### View Logs
```bash
# Application logs
docker-compose logs cloud-file-uploader

# Follow logs in real-time
docker-compose logs -f

# Nginx logs (if using full compose)
docker-compose logs nginx
```

## 💾 Backup & Maintenance

### Important Files to Backup
- `uploads/` directory (your files)
- `docker-compose.yml` (configuration)
- `.env` file (if customized)

### Maintenance Commands
```bash
# Clean up Docker resources
docker system prune

# Update containers
docker-compose pull
docker-compose up -d

# Monitor disk usage
df -h
```