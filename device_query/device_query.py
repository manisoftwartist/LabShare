import subprocess
import xml.etree.ElementTree as ET
import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class DeviceQueryHandler(BaseHTTPRequestHandler):

    def parse_nvidia_xml(self, xml):
        gpu_data = []
        root = ET.fromstring(xml)
        for gpu in root.iter('gpu'):
            current_gpu_data = {
                "name": gpu.find("product_name").text,
                "uuid": gpu.find("uuid").text,
            }

            memory_usage = gpu.find("fb_memory_usage")
            memory = {
                "total": memory_usage.find("total").text,
                "used": memory_usage.find("used").text,
                "free": memory_usage.find("free").text,
            }

            process_block = gpu.find("processes")
            if process_block.text == "N/A":
                current_gpu_data["in_use"] = "na"
            else:
                current_gpu_data["in_use"] = "no"
                for process in process_block.iter("process_info"):
                    if process.find('type').text.lower() == "c":
                        current_gpu_data["in_use"] = "yes"
            current_gpu_data["memory"] = memory
            gpu_data.append(current_gpu_data)
        return gpu_data

    def do_GET(self):
        try:
            raw_gpu_data = subprocess.check_output(["nvidia-smi", "-x", "-q"]).decode('utf-8')
            gpu_data = self.parse_nvidia_xml(raw_gpu_data)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(json.dumps(gpu_data, indent=4), 'utf-8'))
        except Exception as e:
            self.send_error(500)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 12000), DeviceQueryHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
