import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from scraper_runner import run_pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("n8n-trigger")
log_path = "/home/vanrajsinh/Projects/current_affairs_scraper/n8n_trigger.log"
file_handler = logging.FileHandler(log_path)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)

class TriggerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests from n8n"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/run':
            # Extract 'days' parameter, default to 1
            query_params = parse_qs(parsed_path.query)
            days = int(query_params.get('days', [1])[0])
            
            logger.info(f"n8n Triggered: Running scraper for {days} days")
            
            try:
                # We use the current date as the target
                # (You can expand this to accept a specific date if needed)
                target_date = datetime.now()
                
                # Run the pipeline
                result = run_pipeline(target_date)
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    "status": "success",
                    "message": "Scraping and Translation complete",
                    "details": result
                }
                self.wfile.write(json.dumps(response).encode())
                logger.info("Success: Response sent to n8n")
                
            except Exception as e:
                logger.error(f"Error during execution: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Error: {str(e)}".encode())
        else:
            # Handle 404
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Endpoint not found. Use /run?days=1")

def run_server(port=5000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, TriggerHandler)
    print(f"🚀 n8n Trigger Server running on http://localhost:{port}")
    print(f"👉 Use this URL in n8n HTTP Request node: http://localhost:{port}/run?days=1")
    print("Press Ctrl+C to stop.")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
