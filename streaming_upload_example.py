"""
Example of streaming file upload to handle files larger than available RAM
"""
import os
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
        CHUNK_SIZE = 8192  # 8KB chunks - uses minimal RAM
        bytes_written = 0
        
        with open(filepath, 'wb') as f:
            while True:
                chunk = file_stream.read(CHUNK_SIZE)  # Only 8KB in RAM at a time
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
        CHUNK_SIZE = 8192  # 8KB chunks
        
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
