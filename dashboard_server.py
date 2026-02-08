#!/usr/bin/env python3
"""
ListingRadar Dashboard Server
Serves the HTML report via a web interface
Built by Chikara
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import sys
import threading
import time
from pathlib import Path
from simple_radar import SimpleRadar

class ListingRadarHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/dashboard':
            # Generate fresh report
            radar = SimpleRadar()
            report_file = radar.generate_report()
            
            # Serve the report
            with open(report_file, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Content-length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            # Serve static files if needed
            super().do_GET()

def start_dashboard_server(port=8080):
    """Start the dashboard server"""
    os.chdir('/Users/Chikara/.openclaw/workspace/listing-radar')
    
    print(f"✅ ListingRadar Dashboard starting...")
    print(f"📁 Working directory: {os.getcwd()}")
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, ListingRadarHandler)
    
    print(f"🌐 Server running at: http://localhost:{port}")
    print(f"🚀 Dashboard URL: http://localhost:{port}/dashboard")
    print(f"⏹️  Press Ctrl+C to stop")
    print(f"📊 Server ready for requests...")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Stopping server...")
        httpd.shutdown()

if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    start_dashboard_server(port)