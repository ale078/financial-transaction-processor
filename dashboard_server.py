"""Local HTTP server and REST API for the Financial Dashboard."""

import http.server
import socketserver
import json
import urllib.parse
from pathlib import Path
import webbrowser
import threading
import sys
import mimetypes

from src.consolidator import PortfolioConsolidator
from src.exporter import ExcelExporter
from src.market_service import CedearPriceService

PORT = 8050
BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

consolidator = PortfolioConsolidator(INPUT_DIR)
exporter = ExcelExporter(OUTPUT_DIR)
current_portfolio = consolidator.process()
# Pre-generate Excel
exporter.export(current_portfolio)

cedear_service = CedearPriceService(cache_ttl_seconds=300)

class DashboardRequestHandler(http.server.BaseHTTPRequestHandler):
    """Handles static files and financial REST API requests."""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self._serve_file(WEB_DIR / "index.html", "text/html; charset=utf-8")
        elif path == "/api/data":
            self._serve_json(consolidator.to_dict(current_portfolio))
        elif path == "/api/cedears":
            tickers_param = query.get("tickers", [None])[0]
            tickers = [t.strip().upper() for t in tickers_param.split(",")] if tickers_param else [
                "IBIT", "VIST", "COIN", "ASML", "GOOGL", "ETHA", "HUT", "BITF", "OGZD"
            ]
            force = query.get("force", ["0"])[0] in ("1", "true", "True")
            data = cedear_service.get_quotes(tickers=tickers, force_refresh=force)
            self._serve_json(data)
        elif path == "/api/download-excel":
            excel_path = OUTPUT_DIR / "Patrimonio_Consolidado_Alejandro.xlsx"
            if excel_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                self.send_header("Content-Disposition", 'attachment; filename="Patrimonio_Consolidado_Alejandro.xlsx"')
                self.send_header("Content-Length", str(excel_path.stat().st_size))
                self.end_headers()
                with open(excel_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Report not found")
        elif path.startswith("/css/") or path.startswith("/js/") or path.startswith("/img/") or path.startswith("/assets/"):
            clean_path = path.lstrip("/")
            target_file = WEB_DIR / clean_path
            mime_type, _ = mimetypes.guess_type(str(target_file))
            self._serve_file(target_file, mime_type or "text/plain")
        else:
            clean_path = path.lstrip("/")
            target_file = WEB_DIR / clean_path
            if target_file.is_file() and target_file.resolve().is_relative_to(WEB_DIR.resolve()):
                mime_type, _ = mimetypes.guess_type(str(target_file))
                self._serve_file(target_file, mime_type or "application/octet-stream")
            else:
                self.send_error(404, "File not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/refresh":
            global current_portfolio
            try:
                current_portfolio = consolidator.process()
                exporter.export(current_portfolio)
                self._serve_json(consolidator.to_dict(current_portfolio))
            except Exception as e:
                self.send_error(500, f"Error reprocessing portfolio: {e}")
        else:
            self.send_error(404, "Not found")

    def _serve_file(self, file_path: Path, content_type: str):
        if not file_path.exists():
            self.send_error(404, f"File {file_path.name} not found")
            return
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

    def _serve_json(self, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Concise logging
        sys.stdout.write(f"[HTTP {self.address_string()}] {format % args}\n")

def start_server(port=PORT, auto_open=True):
    # Try finding an open port if 8050 is occupied
    actual_port = port
    for p in range(port, port + 10):
        try:
            httpd = socketserver.TCPServer(("", p), DashboardRequestHandler)
            actual_port = p
            break
        except OSError:
            continue

    url = f"http://localhost:{actual_port}"
    print(f"\n=======================================================")
    print(f"      DASHBOARD DE CUENTAS PERSONALES INICIADO")
    print(f"=======================================================")
    print(f"[*] URL: {url}")
    print(f"[*] Presiona Ctrl+C en la terminal para detener el servidor.\n")

    if auto_open:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Deteniendo servidor...")
        httpd.server_close()

if __name__ == "__main__":
    should_open = "--no-open" not in sys.argv
    start_server(PORT, auto_open=should_open)
