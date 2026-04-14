"""
PostgreSQL to MySQL Converter - Web Server
Uses Python's built-in http.server (no external dependencies needed).
Serves both the React frontend and the conversion API.
"""

import http.server
import json
import os
import sys
import uuid
import cgi
import tempfile
import urllib.parse
from pathlib import Path

# Add parent directory to path so we can import converter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from converter import clean_sql, extract_data_only

PORT = 5000
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
# After build, React files will be served from here
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'dist')

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


class ConvertHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for the converter API and static file serving."""

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/convert':
            self._handle_convert()
        else:
            self.send_error(404, 'Not Found')

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path.startswith('/api/download/'):
            self._handle_download(parsed.path)
        elif parsed.path == '/api/health':
            self._send_json({'status': 'ok'})
        else:
            self._serve_frontend(parsed.path)

    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self._set_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_convert(self):
        try:
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' not in content_type:
                self._send_json({'error': 'Content-Type must be multipart/form-data'}, 400)
                return

            # Parse multipart form data
            boundary = content_type.split('boundary=')[1].strip()
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            # Extract file from multipart data
            file_content = self._parse_multipart(body, boundary)

            if not file_content:
                self._send_json({'error': 'No file uploaded'}, 400)
                return

            # Decode file content
            sql_content = file_content.decode('utf-8')

            # Generate unique ID for this conversion
            job_id = str(uuid.uuid4())[:8]

            # Process: Full conversion
            full_converted = clean_sql(sql_content)
            full_filename = f'{job_id}_full_converted.sql'
            full_path = os.path.join(DOWNLOAD_DIR, full_filename)
            with open(full_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(full_converted)

            # Process: Data-only extraction
            data_only = extract_data_only(sql_content)
            data_filename = f'{job_id}_data_only.sql'
            data_path = os.path.join(DOWNLOAD_DIR, data_filename)
            with open(data_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(data_only)

            # Count INSERT statements for stats
            import re
            insert_count = len(re.findall(r'INSERT\s+INTO', sql_content, re.IGNORECASE))

            self._send_json({
                'success': True,
                'job_id': job_id,
                'files': {
                    'full_converted': {
                        'filename': full_filename,
                        'download_url': f'/api/download/{full_filename}',
                        'size': os.path.getsize(full_path)
                    },
                    'data_only': {
                        'filename': data_filename,
                        'download_url': f'/api/download/{data_filename}',
                        'size': os.path.getsize(data_path)
                    }
                },
                'stats': {
                    'original_size': len(sql_content),
                    'insert_statements': insert_count
                }
            })

        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    def _parse_multipart(self, body, boundary):
        """Parse multipart form data and extract the file content."""
        boundary_bytes = f'--{boundary}'.encode()
        parts = body.split(boundary_bytes)

        for part in parts:
            if b'filename=' in part:
                # Find the start of the file content (after double CRLF)
                header_end = part.find(b'\r\n\r\n')
                if header_end != -1:
                    file_data = part[header_end + 4:]
                    # Remove trailing CRLF and boundary markers
                    if file_data.endswith(b'\r\n'):
                        file_data = file_data[:-2]
                    if file_data.endswith(b'--'):
                        file_data = file_data[:-2]
                    if file_data.endswith(b'\r\n'):
                        file_data = file_data[:-2]
                    return file_data
        return None

    def _handle_download(self, path):
        filename = path.replace('/api/download/', '')
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        if not os.path.exists(filepath):
            self.send_error(404, 'File not found')
            return

        with open(filepath, 'rb') as f:
            file_data = f.read()

        self.send_response(200)
        self._set_cors_headers()
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.send_header('Content-Length', str(len(file_data)))
        self.end_headers()
        self.wfile.write(file_data)

    def _serve_frontend(self, path):
        """Serve static frontend files. Falls back to index.html for SPA routing."""
        if path == '/':
            path = '/index.html'

        # Try to serve the file from the frontend dist directory
        file_path = os.path.normpath(os.path.join(FRONTEND_DIR, path.lstrip('/')))

        # Security: make sure the path is within FRONTEND_DIR
        if not file_path.startswith(os.path.normpath(FRONTEND_DIR)):
            self.send_error(403, 'Forbidden')
            return

        if os.path.isfile(file_path):
            self._serve_file(file_path)
        else:
            # SPA fallback: serve index.html
            index_path = os.path.join(FRONTEND_DIR, 'index.html')
            if os.path.isfile(index_path):
                self._serve_file(index_path)
            else:
                self.send_error(404, 'Frontend not built. Run: cd frontend && npm run build')

    def _serve_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.svg': 'image/svg+xml',
            '.png': 'image/png',
            '.ico': 'image/x-icon',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
        }
        content_type = content_types.get(ext, 'application/octet-stream')

        with open(file_path, 'rb') as f:
            data = f.read()

        self.send_response(200)
        self._set_cors_headers()
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[Server] {args[0]} {args[1]}")


def main():
    server_address = ('', PORT)
    httpd = http.server.HTTPServer(server_address, ConvertHandler)
    print(f"SQL Converter Server running on http://localhost:{PORT}")
    print("API Endpoints:")
    print("  POST /api/convert")
    print("  GET  /api/download/*")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.server_close()


if __name__ == '__main__':
    main()
