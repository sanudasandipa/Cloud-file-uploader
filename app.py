import os
import shutil
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import mimetypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
# Temporarily hardcode 3GB to avoid env loading issues
MAX_FILE_SIZE = 3221225472  # 3GB in bytes
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

print(f"Server started with MAX_FILE_SIZE: {MAX_FILE_SIZE:,} bytes ({MAX_FILE_SIZE / (1024**3):.1f}GB)")

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_file_info(filepath):
    """Get file information including size, modified date, etc."""
    try:
        stat = os.stat(filepath)
        return {
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'type': mimetypes.guess_type(filepath)[0] or 'unknown'
        }
    except OSError:
        return None

def format_file_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

def check_storage_space(file_size):
    """Check if there's enough storage space for the upload"""
    try:
        disk_usage = shutil.disk_usage(UPLOAD_FOLDER)
        free_space = disk_usage.free
        
        # Require at least 5GB free space after upload
        min_free_space = 5 * 1024 * 1024 * 1024  # 5GB
        
        if free_space - file_size < min_free_space:
            return False, f"Insufficient storage space. Need at least 5GB free after upload."
        
        return True, None
    except Exception as e:
        return False, f"Error checking storage: {str(e)}"

def get_memory_usage():
    """Get current memory usage (Linux only)"""
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        
        for line in meminfo.split('\n'):
            if 'MemAvailable:' in line:
                available_kb = int(line.split()[1])
                available_mb = available_kb / 1024
                return available_mb
        return None
    except:
        return None

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/files', methods=['GET'])
def list_files():
    """List all uploaded files with their metadata"""
    try:
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                file_info = get_file_info(filepath)
                if file_info:
                    files.append({
                        'name': filename,
                        'size': file_info['size'],
                        'size_formatted': format_file_size(file_info['size']),
                        'modified': file_info['modified'],
                        'type': file_info['type']
                    })
        
        # Sort by modified date (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': files,
            'total_files': len(files)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload a file to the server"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if file:
            # Check file size from the request
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            # Check storage space
            has_space, storage_error = check_storage_space(file_size)
            if not has_space:
                return jsonify({
                    'success': False,
                    'error': storage_error
                }), 507  # Insufficient Storage
            
            # Secure the filename
            filename = secure_filename(file.filename)
            
            # Check if file already exists and add number suffix if needed
            original_filename = filename
            counter = 1
            while os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
                name, ext = os.path.splitext(original_filename)
                filename = f"{name}_{counter}{ext}"
                counter += 1
            
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            file_info = get_file_info(filepath)
            
            return jsonify({
                'success': True,
                'message': f'File "{filename}" uploaded successfully',
                'file': {
                    'name': filename,
                    'size': file_info['size'],
                    'size_formatted': format_file_size(file_info['size']),
                    'modified': file_info['modified'],
                    'type': file_info['type']
                }
            })
    
    except RequestEntityTooLarge:
        return jsonify({
            'success': False,
            'error': f'File too large. Maximum size is {format_file_size(MAX_FILE_SIZE)}'
        }), 413
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download a file from the server"""
    try:
        filename = secure_filename(filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a file from the server"""
    try:
        filename = secure_filename(filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': f'File "{filename}" deleted successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/storage', methods=['GET'])
def get_storage_info():
    """Get storage usage information"""
    try:
        total_size = 0
        file_count = 0
        
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                total_size += os.path.getsize(filepath)
                file_count += 1
        
        # Get disk usage
        disk_usage = shutil.disk_usage(UPLOAD_FOLDER)
        
        # Get memory info (for monitoring on low-RAM server)
        available_memory = get_memory_usage()
        
        storage_info = {
            'used_space': total_size,
            'used_space_formatted': format_file_size(total_size),
            'total_space': disk_usage.total,
            'total_space_formatted': format_file_size(disk_usage.total),
            'free_space': disk_usage.free,
            'free_space_formatted': format_file_size(disk_usage.free),
            'file_count': file_count,
            'max_file_size': MAX_FILE_SIZE,
            'max_file_size_formatted': format_file_size(MAX_FILE_SIZE)
        }
        
        if available_memory:
            storage_info['available_memory_mb'] = round(available_memory, 1)
        
        return jsonify({
            'success': True,
            'storage': storage_info
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Check if running in Docker (production mode)
    debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
