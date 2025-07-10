import os
import shutil
import uuid
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for, abort
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

# Initialize database for file sharing
def init_database():
    """Initialize SQLite database for file sharing"""
    conn = sqlite3.connect('file_shares.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            share_id TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            download_count INTEGER DEFAULT 0,
            max_downloads INTEGER,
            password TEXT,
            created_by TEXT DEFAULT 'anonymous'
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

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
    """Check if there's enough storage space for the file"""
    try:
        disk_usage = shutil.disk_usage(UPLOAD_FOLDER)
        
        # Leave 1GB buffer space
        required_space = file_size + (1024 * 1024 * 1024)  # 1GB buffer
        
        if disk_usage.free < required_space:
            return False, f"Insufficient storage space. Need {format_file_size(required_space)}, only {format_file_size(disk_usage.free)} available"
        
        return True, None
    except Exception as e:
        return False, f"Error checking storage space: {str(e)}"

def get_memory_usage():
    """Get available memory in MB"""
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemAvailable:'):
                    # Extract the number and convert from KB to MB
                    mem_kb = int(line.split()[1])
                    return mem_kb / 1024
    except:
        return None

def generate_share_id():
    """Generate a unique share ID"""
    return str(uuid.uuid4())[:8]

def create_file_share(filename, expires_hours=None, max_downloads=None, password=None):
    """Create a new file share entry in database"""
    share_id = generate_share_id()
    expires_at = None
    
    if expires_hours:
        expires_at = datetime.now() + timedelta(hours=expires_hours)
    
    conn = sqlite3.connect('file_shares.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO file_shares (share_id, filename, expires_at, max_downloads, password)
            VALUES (?, ?, ?, ?, ?)
        ''', (share_id, filename, expires_at, max_downloads, password))
        
        conn.commit()
        return share_id
    except sqlite3.IntegrityError:
        # If share_id already exists, try again
        return create_file_share(filename, expires_hours, max_downloads, password)
    finally:
        conn.close()

def get_file_share(share_id):
    """Get file share information from database"""
    conn = sqlite3.connect('file_shares.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT share_id, filename, created_at, expires_at, download_count, max_downloads, password
        FROM file_shares WHERE share_id = ?
    ''', (share_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'share_id': result[0],
            'filename': result[1],
            'created_at': result[2],
            'expires_at': result[3],
            'download_count': result[4],
            'max_downloads': result[5],
            'password': result[6]
        }
    return None

def increment_download_count(share_id):
    """Increment download count for a share"""
    conn = sqlite3.connect('file_shares.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE file_shares SET download_count = download_count + 1
        WHERE share_id = ?
    ''', (share_id,))
    
    conn.commit()
    conn.close()

def get_file_shares_by_filename(filename):
    """Get all active shares for a file"""
    conn = sqlite3.connect('file_shares.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT share_id, filename, created_at, expires_at, download_count, max_downloads, password
        FROM file_shares 
        WHERE filename = ? AND (expires_at IS NULL OR expires_at > datetime('now'))
        ORDER BY created_at DESC
    ''', (filename,))
    
    results = cursor.fetchall()
    conn.close()
    
    shares = []
    for result in results:
        shares.append({
            'share_id': result[0],
            'filename': result[1],
            'created_at': result[2],
            'expires_at': result[3],
            'download_count': result[4],
            'max_downloads': result[5],
            'has_password': bool(result[6])
        })
    
    return shares

def delete_file_share(share_id):
    """Delete a file share"""
    conn = sqlite3.connect('file_shares.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM file_shares WHERE share_id = ?', (share_id,))
    conn.commit()
    conn.close()

def is_share_valid(share_data):
    """Check if a share is still valid"""
    if not share_data:
        return False, "Share not found"
    
    # Check expiration
    if share_data['expires_at']:
        expires_at = datetime.fromisoformat(share_data['expires_at'].replace('Z', '+00:00'))
        if expires_at < datetime.now():
            return False, "Share has expired"
    
    # Check download limit
    if share_data['max_downloads']:
        if share_data['download_count'] >= share_data['max_downloads']:
            return False, "Download limit reached"
    
    return True, "Valid"

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
            
            # Check memory availability for upload
            has_memory, memory_message = check_memory_for_upload(file_size)
            
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
            
            # Use streaming upload if recommended
            if not has_memory:
                # Stream save the file in chunks
                bytes_written, error = stream_save_file(file, filepath)
                if error:
                    return jsonify({
                        'success': False,
                        'error': f"Error saving file: {error}"
                    }), 500
                
                file_info = get_file_info(filepath)
                
                return jsonify({
                    'success': True,
                    'message': f'File "{filename}" uploaded successfully (streaming)',
                    'file': {
                        'name': filename,
                        'size': file_info['size'],
                        'size_formatted': format_file_size(file_info['size']),
                        'modified': file_info['modified'],
                        'type': file_info['type']
                    }
                })
            
            # Save the file normally
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

@app.route('/api/share', methods=['POST'])
def create_share():
    """Create a shareable link for a file"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        expires_hours = data.get('expires_hours')
        max_downloads = data.get('max_downloads')
        password = data.get('password')
        
        if not filename:
            return jsonify({
                'success': False,
                'error': 'Filename is required'
            }), 400
        
        # Check if file exists
        filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        # Create share
        share_id = create_file_share(filename, expires_hours, max_downloads, password)
        
        share_url = request.host_url + f'share/{share_id}'
        
        return jsonify({
            'success': True,
            'share_id': share_id,
            'share_url': share_url,
            'message': 'Share link created successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/shares/<filename>', methods=['GET'])
def get_file_shares(filename):
    """Get all active shares for a file"""
    try:
        filename = secure_filename(filename)
        shares = get_file_shares_by_filename(filename)
        
        # Format the shares for frontend
        formatted_shares = []
        for share in shares:
            share_url = request.host_url + f'share/{share["share_id"]}'
            formatted_share = {
                'share_id': share['share_id'],
                'share_url': share_url,
                'created_at': share['created_at'],
                'expires_at': share['expires_at'],
                'download_count': share['download_count'],
                'max_downloads': share['max_downloads'],
                'has_password': share['has_password']
            }
            formatted_shares.append(formatted_share)
        
        return jsonify({
            'success': True,
            'shares': formatted_shares
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/share/<share_id>', methods=['DELETE'])
def delete_share(share_id):
    """Delete a share link"""
    try:
        share_data = get_file_share(share_id)
        if not share_data:
            return jsonify({
                'success': False,
                'error': 'Share not found'
            }), 404
        
        delete_file_share(share_id)
        
        return jsonify({
            'success': True,
            'message': 'Share deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/share/<share_id>')
def shared_file_page(share_id):
    """Display shared file download page"""
    try:
        share_data = get_file_share(share_id)
        valid, message = is_share_valid(share_data)
        
        if not valid:
            abort(404)
        
        file_info = get_file_info(os.path.join(UPLOAD_FOLDER, share_data['filename']))
        if file_info:
            file_info['size_formatted'] = format_file_size(file_info['size'])
        
        return render_template('shared_file.html', 
                             share=share_data, 
                             file_info=file_info,
                             share_id=share_id)
        
    except Exception as e:
        abort(404)

@app.route('/api/share/<share_id>/download', methods=['POST'])
def download_shared_file(share_id):
    """Download a shared file"""
    try:
        share_data = get_file_share(share_id)
        valid, message = is_share_valid(share_data)
        
        if not valid:
            return jsonify({
                'success': False,
                'error': message
            }), 403
        
        # Check password if required
        if share_data['password']:
            data = request.get_json() or {}
            provided_password = data.get('password')
            
            if not provided_password or provided_password != share_data['password']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid password'
                }), 401
        
        filename = share_data['filename']
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        # Increment download count
        increment_download_count(share_id)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def check_memory_for_upload(file_size):
    """Check if we have enough memory for traditional upload, recommend streaming if not"""
    available_memory_mb = get_memory_usage()
    
    if available_memory_mb is None:
        return True, "Cannot determine memory usage"
    
    # Convert file size to MB
    file_size_mb = file_size / (1024 * 1024)
    
    # If file is larger than 50% of available memory, recommend streaming
    if file_size_mb > (available_memory_mb * 0.5):
        return False, f"File too large for memory ({file_size_mb:.1f}MB), only {available_memory_mb:.1f}MB available. Use streaming upload."
    
    return True, None

def stream_save_file(file_storage, filepath, chunk_size=8192):
    """Save uploaded file in chunks to minimize RAM usage"""
    bytes_written = 0
    
    try:
        with open(filepath, 'wb') as f:
            while True:
                # Read small chunks to minimize RAM usage
                chunk = file_storage.stream.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                bytes_written += len(chunk)
        
        return bytes_written, None
    except Exception as e:
        # Clean up partial file on error
        if os.path.exists(filepath):
            os.remove(filepath)
        return 0, str(e)

if __name__ == '__main__':
    init_database()
    app.run(host='0.0.0.0', port=5000, debug=True)
