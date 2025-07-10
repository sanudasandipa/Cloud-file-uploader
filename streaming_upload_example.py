"""
Example of streaming file upload to handle files larger than available RAM
"""
import os
import time
import logging
from flask import Flask, request, jsonify
from werkzeug.datastructures import FileStorage

def stream_file_upload():
    """Handle large file uploads by streaming directly to disk"""
    try:
        # Get the file from request without loading into memory
        file_stream = request.stream
        content_length = request.content_length
        
        if not content_length:
            return jsonify({'error': 'Content-Length header required'}), 400
            
        # Check if we have enough disk space
        if not check_storage_space(content_length):
            return jsonify({'error': 'Insufficient storage space'}), 507
        
        filename = request.headers.get('X-Filename', 'uploaded_file')
        filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        
        # Stream file directly to disk in chunks
        CHUNK_SIZE = 65536  # 64KB chunks - better performance, still minimal RAM
        bytes_written = 0
        
        with open(filepath, 'wb') as f:
            while True:
                chunk = file_stream.read(CHUNK_SIZE)  # Only 64KB in RAM at a time
                if not chunk:
                    break
                f.write(chunk)
                bytes_written += len(chunk)
                
                # Optional: Send progress updates via WebSocket/SSE
                # progress = (bytes_written / content_length) * 100
        
        return jsonify({
            'success': True,
            'filename': filename,
            'size': bytes_written
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Alternative: Using werkzeug's streaming
def werkzeug_stream_upload():
    """Using werkzeug's built-in streaming capabilities"""
    
    def save_chunks_to_file(file_storage, filepath):
        """Save file in chunks to minimize RAM usage"""
        CHUNK_SIZE = 65536  # 64KB chunks - improved performance
        
        with open(filepath, 'wb') as f:
            while True:
                chunk = file_storage.stream.read(CHUNK_SIZE)
                if not chunk:
                    break
                f.write(chunk)
    
    file = request.files['file']
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        save_chunks_to_file(file, filepath)
        return jsonify({'success': True})

def optimized_large_file_upload():
    """Optimized streaming upload with performance tracking for large files (43GB+)"""
    try:
        file_stream = request.stream
        content_length = request.content_length
        
        if not content_length:
            return jsonify({'error': 'Content-Length header required'}), 400
            
        # Check if we have enough disk space (with 10% safety margin)
        if not check_storage_space(content_length * 1.1):
            return jsonify({'error': 'Insufficient storage space'}), 507
        
        filename = request.headers.get('X-Filename', 'uploaded_file')
        filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        
        # Optimized chunk size for large files
        CHUNK_SIZE = 65536  # 64KB - optimal balance of performance and RAM usage
        bytes_written = 0
        start_time = time.time()
        last_progress_time = start_time
        
        # Log start of large upload
        file_size_gb = content_length / (1024**3)
        logging.info(f"Starting large file upload: {filename} ({file_size_gb:.2f}GB)")
        
        with open(filepath, 'wb') as f:
            while True:
                chunk = file_stream.read(CHUNK_SIZE)
                if not chunk:
                    break
                    
                f.write(chunk)
                bytes_written += len(chunk)
                
                # Progress tracking for large files (every 1GB or 5 minutes)
                current_time = time.time()
                if (bytes_written % (1024**3) == 0 or  # Every 1GB
                    current_time - last_progress_time > 300):  # Every 5 minutes
                    
                    elapsed = current_time - start_time
                    speed_mbps = (bytes_written * 8) / (elapsed * 1000000) if elapsed > 0 else 0
                    progress_pct = (bytes_written / content_length) * 100
                    
                    logging.info(f"Upload progress: {progress_pct:.1f}% "
                               f"({bytes_written/(1024**3):.2f}GB), "
                               f"Speed: {speed_mbps:.2f} Mbps")
                    
                    last_progress_time = current_time
        
        total_time = time.time() - start_time
        avg_speed_mbps = (bytes_written * 8) / (total_time * 1000000)
        
        logging.info(f"Upload completed: {filename} "
                    f"({bytes_written/(1024**3):.2f}GB) "
                    f"in {total_time/3600:.2f} hours, "
                    f"avg speed: {avg_speed_mbps:.2f} Mbps")
        
        return jsonify({
            'success': True,
            'filename': filename,
            'size': bytes_written,
            'size_gb': bytes_written / (1024**3),
            'upload_time_hours': total_time / 3600,
            'average_speed_mbps': avg_speed_mbps
        })
        
    except IOError as e:
        logging.error(f"I/O error during upload: {e}")
        # Clean up partial file
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': f'I/O error: {str(e)}'}), 500
        
    except Exception as e:
        logging.error(f"Upload error: {e}")
        # Clean up partial file
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e)}), 500
