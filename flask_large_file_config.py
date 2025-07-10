"""
Flask configuration for handling large files with limited RAM
"""
from flask import Flask
import tempfile
import os

app = Flask(__name__)

# Configuration for large file handling
app.config.update(
    # Maximum request size (3GB)
    MAX_CONTENT_LENGTH=3 * 1024 * 1024 * 1024,
    
    # Use temporary directory on disk instead of RAM
    # This tells Flask to stream large files to temp files
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
)

# Set temporary directory to a location with sufficient disk space
tempfile.tempdir = '/tmp'  # Or your preferred temp location

# Additional server configuration needed:
"""
For production deployment, you also need to configure:

1. **Nginx Configuration** (if using nginx):
   ```nginx
   client_max_body_size 3G;
   client_body_timeout 300s;
   client_header_timeout 300s;
   proxy_read_timeout 300s;
   proxy_send_timeout 300s;
   ```

2. **Gunicorn Configuration** (if using gunicorn):
   ```bash
   gunicorn --timeout 300 --worker-class sync --workers 1 app:app
   ```
   
3. **System-level settings**:
   - Increase swap space if needed
   - Monitor disk I/O during uploads
   - Set up proper logging for large uploads
"""
