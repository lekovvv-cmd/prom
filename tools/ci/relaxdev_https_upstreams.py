"""Tiny TLS upstreams for the RelaxDev nginx CI smoke test."""

import ssl
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


def serve(port: int, label: str, certificate: str, key: str) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            body = f"{label}:{self.path}:{self.headers.get('X-Request-ID', '')}".encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = HTTPServer(("127.0.0.1", port), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certificate, key)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    server.serve_forever()


if __name__ == "__main__":
    cert, secret = sys.argv[1:3]
    for port, label in ((18081, "access"), (18082, "projects")):
        threading.Thread(target=serve, args=(port, label, cert, secret), daemon=True).start()
    threading.Event().wait()
