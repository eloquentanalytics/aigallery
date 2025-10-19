from http.server import BaseHTTPRequestHandler
import json
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # Set response headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # Route handling
        if path == '/api' or path == '/api/':
            response = {
                "message": "AI Gallery API",
                "status": "running",
                "version": "1.0.0",
                "environment": "vercel"
            }
        elif path == '/api/health':
            response = {
                "status": "ok",
                "message": "AI Gallery is running on Vercel"
            }
        elif path == '/api/test':
            response = {
                "test": "success",
                "message": "Basic HTTP handler working"
            }
        else:
            response = {
                "error": "Not found",
                "path": path
            }

        # Send JSON response
        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        self.do_GET()  # Handle POST same as GET for now