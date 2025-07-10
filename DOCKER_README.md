# Cloud File Uploader - Docker Setup

This project is now configured to run with Docker for easy deployment on Ubuntu servers.

## Quick Start

### 1. Install Docker (Ubuntu Server)
```bash
# Update system
sudo apt update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group (optional)
sudo usermod -aG docker $USER
```

### 2. Deploy the Application
```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

## Docker Configuration

### Files Created:
- `Dockerfile` - Container configuration
- `docker-compose.yml` - Multi-container setup
- `nginx.conf` - Nginx reverse proxy configuration
- `.dockerignore` - Files to exclude from Docker build
- `deploy.sh` - Automated deployment script
- `cleanup.sh` - Cleanup script

### Container Setup:
- **App Container**: Python Flask application on port 5000
- **Nginx Container**: Reverse proxy on port 80/443
- **Volumes**: Persistent storage for uploads and logs

## Access Points

After deployment, your application will be available at:
- `http://your-server-ip` (via Nginx)
- `http://your-server-ip:5000` (direct Flask app)

## Management Commands

```bash
# View logs
docker-compose logs -f

# Stop application
docker-compose down

# Restart application
docker-compose restart

# Rebuild and restart
docker-compose up --build -d

# View running containers
docker-compose ps
```

## Production Considerations

### SSL/HTTPS Setup
1. Obtain SSL certificates (Let's Encrypt recommended)
2. Place certificates in `ssl/` directory
3. Update `nginx.conf` to include SSL configuration

### Firewall Configuration
```bash
# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Optional: Allow direct Flask access
sudo ufw allow 5000
```

### Environment Variables
Create a `.env` file for production settings:
```
FLASK_ENV=production
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=3221225472
```

### Resource Limits
For production, consider adding resource limits to `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
```

## File Upload Limits
- Default: 3GB max file size
- Configured in both Flask app and Nginx
- Modify `MAX_FILE_SIZE` and `client_max_body_size` as needed

## Backup
Important directories to backup:
- `uploads/` - User uploaded files
- `logs/` - Application logs
