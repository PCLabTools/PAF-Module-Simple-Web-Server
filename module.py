"""
file: module.py
description: Provides a simple HTTP server module for the Python Actor Framework (PAF).
author: PCLabTools (https://github.com/PCLabTools)
"""

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from time import sleep
from typing import Optional
from urllib.parse import unquote, urlparse

from paf.communication import Message, Protocol, Module


class _ReusableThreadingHTTPServer(ThreadingHTTPServer):
    """Threaded HTTP server with address reuse enabled for local development."""

    allow_reuse_address = True
    daemon_threads = True


class WebServer(Module):
    """A simple HTTP web server module for the PAF framework."""

    def __init__(
        self,
        address: str,
        protocol: Protocol,
        debug: Optional[int] = 0,
        host: str = "127.0.0.1",
        port: int = 8000,
    ):
        """Initialise the module and start the web server.

        Args:
            address (str): The address of the module.
            protocol (Protocol): The protocol instance.
            debug (Optional[int]): Debug level.
            host (str): Host address to bind the HTTP server to.
            port (int): Preferred TCP port for the HTTP server.
        """
        self.debug = debug or 0
        self.host = host
        self.port = port
        self.www_dir = Path(__file__).resolve().parent / "www"
        self.http_server: Optional[_ReusableThreadingHTTPServer] = None
        self.server_thread: Optional[Thread] = None
        super().__init__(address, protocol)
        self.start_http_server()

    @property
    def server_url(self) -> str:
        """Return the URL where the local HTTP server can be reached."""
        return f"http://{self.host}:{self.port}"

    def __del__(self):
        """Ensure the HTTP server is stopped during cleanup."""
        self.stop_http_server()
        super().__del__()

    def _build_request_handler(self):
        """Create a request handler bound to this module instance."""
        parent = self

        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                path = unquote(urlparse(self.path).path)
                if path == "/api/modules":
                    return self._send_json(
                        {
                            "modules": sorted(parent.protocol.get_registered_modules()),
                            "webserver": parent.address,
                            "url": parent.server_url,
                        }
                    )
                return self._serve_static_file(path)

            def do_POST(self):
                path = urlparse(self.path).path
                if path == "/api/shutdown":
                    content_length = int(self.headers.get("Content-Length", "0"))
                    if content_length:
                        self.rfile.read(content_length)
                    self._send_json(
                        {
                            "success": True,
                            "message": "Shutdown broadcast sent to all registered modules.",
                        }
                    )
                    Thread(target=parent.protocol.broadcast_message, args=("shutdown",), daemon=True).start()
                    return
                self.send_error(HTTPStatus.NOT_FOUND, "Resource not found")

            def _serve_static_file(self, path: str):
                requested = "index.html" if path in ("", "/", "/index.html") else path.lstrip("/")
                file_path = (parent.www_dir / requested).resolve()

                if not file_path.is_file() or parent.www_dir.resolve() not in file_path.parents:
                    self.send_error(HTTPStatus.NOT_FOUND, "Resource not found")
                    return

                content = file_path.read_bytes()
                content_type, _ = mimetypes.guess_type(str(file_path))
                if content_type is None:
                    content_type = "application/octet-stream"
                elif content_type.startswith("text/"):
                    content_type = f"{content_type}; charset=utf-8"

                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

            def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK):
                content = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

            def log_message(self, format, *args):
                if parent.debug >= 2:
                    super().log_message(format, *args)

        return RequestHandler

    def start_http_server(self):
        """Start the HTTP server in a dedicated thread."""
        if self.http_server is not None:
            return

        handler = self._build_request_handler()

        try:
            self.http_server = _ReusableThreadingHTTPServer((self.host, self.port), handler)
        except OSError:
            self.http_server = _ReusableThreadingHTTPServer((self.host, 0), handler)

        self.port = int(self.http_server.server_address[1])
        self.server_thread = Thread(
            target=self.http_server.serve_forever,
            name=f"{self.address}-http-server",
            daemon=True,
        )
        self.server_thread.start()

        if self.debug:
            print(f"{self.__class__.__name__} ({self.address}): Serving {self.server_url}")

    def stop_http_server(self):
        """Stop the HTTP server if it is running."""
        if self.http_server is None:
            return

        try:
            self.http_server.shutdown()
            self.http_server.server_close()
        finally:
            self.http_server = None

        if self.server_thread is not None and self.server_thread.is_alive():
            self.server_thread.join(timeout=1.0)
        self.server_thread = None

    def handle_message(self, message: Message) -> bool:
        """Handle incoming PAF messages."""
        if self.debug:
            print(f"{self.__class__.__name__} ({self.address}): Handling message: {message}")

        if message.command == "custom_action":
            return self.message_custom_action(message)
        if message.command == "shutdown":
            self.stop_http_server()
            return super().handle_message(message)
        return super().handle_message(message)

    def background_task(self):
        """Optional background task loop for compatibility with the PAF template."""
        while self.background_task_running:
            if self.debug:
                print(f"{self.__class__.__name__} ({self.address}): Running background task.")
            sleep(1)

    def message_custom_action(self, message: Message) -> bool:
        """Handle the custom_action message without interrupting the module."""
        if self.debug:
            print(f"{self.__class__.__name__} ({self.address}): Handling custom action message: {message}")
        return False