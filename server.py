#!/usr/bin/env python3
import os
import json
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

class CRMHandler(BaseHTTPRequestHandler):
    def send_json_error(self, status_code, code, message, details=None):
        try:
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            payload = {'error': {'code': code, 'message': message}}
            if details is not None:
                payload['error']['details'] = details
            self.wfile.write(json.dumps(payload).encode('utf-8'))
        except (ConnectionAbortedError, BrokenPipeError):
            pass

    def serve_404(self):
        content = (
            "<!doctype html><html><head><meta charset='utf-8'><title>404 Not Found" 
            "</title><style>body{font-family:sans-serif;padding:2rem;color:#333}" 
            "h1{margin:0 0 0.5rem}code{background:#f5f5f5;padding:0.2rem 0.4rem}" 
            "a{color:#0066cc}</style></head><body>"
            "<h1>Page Not Found</h1>"
            f"<p>The requested path <code>{self.path}</code> was not found.</p>"
            "<p><a href='/'>Go to Login</a></p>"
            "</body></html>"
        )
        self.send_response(404)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def do_GET(self):
        parsed = urlparse(self.path)
        req_path = parsed.path
        print(f"GET: {req_path}{('?' + parsed.query) if parsed.query else ''}")

        if req_path == '/' or req_path == '/index.html':
            self.serve_login()
        elif req_path.startswith('/static/'):
            self.serve_static(req_path)
        elif req_path.startswith('/assets/'):
            self.serve_static(req_path)
        elif req_path.startswith('/employee/'):
            parts = req_path.strip('/').split('/')
            if len(parts) >= 3:
                page = parts[2]
                if page == 'log':
                    self.serve_html('/activity_logging_page/code.html')
                    return
                if page in ('dmr', 'daily-report'):
                    self.serve_html('/daily_work_report/code.html')
                    return
                if page == 'dashboard':
                    self.serve_html('/employee_dashboard_page/code.html')
                    return
            self.serve_404()
        elif req_path.endswith('.html'):
            self.serve_html(req_path)
        elif req_path.startswith('/api/'):
            self.handle_api(req_path)
        elif req_path == '/@vite/client':
            self.send_response(200)
            self.send_header('Content-Type', 'application/javascript')
            self.end_headers()
            self.wfile.write(b'')
        else:
            self.serve_404()
    
    def do_POST(self):
        parsed = urlparse(self.path)
        req_path = parsed.path
        if req_path.startswith('/api/'):
            self.handle_api(req_path)
        else:
            self.serve_404()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def serve_login(self):
        try:
            login_file = Path(__file__).parent / 'login_page' / 'code.html'
            with open(login_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            print(f"Error serving login: {e}")
            self.serve_404()
    
    def serve_static(self, req_path=None):
        try:
            path = req_path or urlparse(self.path).path
            base = Path(__file__).parent
            if path.startswith('/assets/'):
                rel = path[len('/assets/'):]
                base_dir = base / 'assets'
                file_path = (base_dir / rel).resolve()
            elif path.startswith('/static/'):
                rel = path[len('/static/'):]
                base_dir = base / 'static'
                file_path = (base_dir / rel).resolve()
            else:
                file_path = (base / path.lstrip('/')).resolve()
                base_dir = base
            
            if not str(file_path).startswith(str(base_dir.resolve())):
                self.serve_404()
                return
            
            if not file_path.exists():
                self.serve_404()
                return
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Set content type
            if file_path.suffix == '.png':
                content_type = 'image/png'
            elif file_path.suffix == '.jpg' or file_path.suffix == '.jpeg':
                content_type = 'image/jpeg'
            elif file_path.suffix == '.svg':
                content_type = 'image/svg+xml'
            elif file_path.suffix == '.css':
                content_type = 'text/css'
            elif file_path.suffix == '.js':
                content_type = 'application/javascript'
            else:
                content_type = 'application/octet-stream'
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"Error serving static file: {e}")
            self.serve_404()
    
    def serve_html(self, req_path=None):
        try:
            path = req_path or urlparse(self.path).path
            file_path = Path(__file__).parent / path.lstrip('/')
            
            if not file_path.exists():
                self.serve_404()
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            print(f"Error serving HTML: {e}")
            self.serve_404()
    
    def handle_api(self, req_path=None):
        try:
            parsed = urlparse(self.path)
            path = req_path or parsed.path
            query = parsed.query
            target_base = os.getenv('API_PROXY_TARGET', 'http://localhost:8000')
            target_url = f"{target_base}{path}{('?' + query) if query else ''}"

            body = b''
            if self.command in ('POST', 'PUT', 'PATCH'):
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length > 0 else b''

            headers = {}
            for key in ('Authorization', 'Content-Type', 'Accept'):
                val = self.headers.get(key)
                if val:
                    headers[key] = val

            req = Request(target_url, data=body if body else None, method=self.command)
            for k, v in headers.items():
                req.add_header(k, v)

            try:
                with urlopen(req) as resp:
                    status = getattr(resp, 'status', 200)
                    content_type = resp.headers.get('Content-Type', 'application/json')
                    data = resp.read()

                    try:
                        self.send_response(status)
                        self.send_header('Content-Type', content_type)
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(data)
                    except (ConnectionAbortedError, BrokenPipeError):
                        pass

            except HTTPError as e:
                try:
                    status = e.code
                    self.send_response(status)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    error_data = {"error": {"code": "api_error", "message": f"API returned {status}"}}
                    self.wfile.write(json.dumps(error_data).encode('utf-8'))
                except (ConnectionAbortedError, BrokenPipeError):
                    pass
                
            except URLError as e:
                print(f"API connection failed: {e}")
                try:
                    self.send_json_error(503, "service_unavailable", "Backend service unavailable")
                except (ConnectionAbortedError, BrokenPipeError):
                    pass
                
        except (ConnectionAbortedError, BrokenPipeError):
            pass
        except Exception as e:
            print(f"API proxy error: {e}")
            try:
                self.send_json_error(500, "proxy_error", "Request processing failed")
            except (ConnectionAbortedError, BrokenPipeError):
                pass

def run_server():
    port = int(os.getenv('PORT', '3000'))
    server = HTTPServer(('0.0.0.0', port), CRMHandler)
    print(f"CRM Server running on http://localhost:{port}")
    print(f"Backend API proxy: {os.getenv('API_PROXY_TARGET', 'http://localhost:8001')}")
    print("Ready for connections!")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped")
        server.server_close()

if __name__ == '__main__':
    run_server()