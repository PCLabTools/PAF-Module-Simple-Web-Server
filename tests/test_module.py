"""
Unit tests for the WebServer class
"""
import unittest
import time
import json
from urllib import request
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from paf.communication import Protocol, Message, Module
from paf.modules.webserver.module import WebServer


class TestWebServer(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.protocol = Protocol()

    def tearDown(self):
        """Clean up test fixtures"""
        # Send shutdown to all registered modules to stop their threads
        for module_name in self.protocol.get_registered_modules():
            try:
                self.protocol.send_action(module_name, "shutdown")
            except:
                pass
        # Wait a bit for threads to finish
        time.sleep(0.1)
        # Clean up any registered modules
        for module_name in self.protocol.get_registered_modules():
            try:
                self.protocol.unregister_module(module_name)
            except:
                pass
        del self.protocol

    def test_init(self):
        """Test WebServer initialization"""
        module = WebServer("test_webserver", self.protocol, debug=0)
        self.assertEqual(module.address, "test_webserver")
        self.assertEqual(module.protocol, self.protocol)
        self.assertEqual(module.debug, 0)
        self.assertIn("test_webserver", self.protocol.registered_modules)
        self.assertTrue(module.thread.is_alive())
        self.assertFalse(module.background_task_running)

        # Clean up
        self.protocol.send_action("test_webserver", "shutdown")
        module.thread.join(timeout=1.0)

    def test_init_with_debug(self):
        """Test WebServer initialization with debug enabled"""
        module = WebServer("test_webserver_debug", self.protocol, debug=1)
        self.assertEqual(module.debug, 1)
        
        # Clean up
        self.protocol.send_action("test_webserver_debug", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_custom_action(self):
        """Test handle_message with custom_action command"""
        module = WebServer("test_webserver", self.protocol, debug=0)
        msg = Message("test_webserver", "custom_action", {"key": "value"})
        
        result = module.handle_message(msg)
        self.assertFalse(result)  # Should return False to continue running
        
        # Clean up
        self.protocol.send_action("test_webserver", "shutdown")
        module.thread.join(timeout=1.0)

    def test_message_custom_action(self):
        """Test message_custom_action method directly"""
        module = WebServer("test_webserver", self.protocol, debug=0)
        msg = Message("test_webserver", "custom_action", {"data": "test"})
        
        result = module.message_custom_action(msg)
        self.assertFalse(result)  # Returns False
        
        # Clean up
        self.protocol.send_action("test_webserver", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_unknown(self):
        """Test handle_message with unknown command raises NotImplementedError"""
        module = WebServer("test_webserver", self.protocol, debug=0)
        msg = Message("test_webserver", "unknown_command")
        
        with self.assertRaises(NotImplementedError):
            module.handle_message(msg)
        
        # Clean up
        self.protocol.send_action("test_webserver", "shutdown")
        module.thread.join(timeout=1.0)

    def test_background_task_running(self):
        """Test background task runs when enabled"""
        module = WebServer("test_webserver", self.protocol, debug=0)
        
        # Start background task
        self.protocol.send_action("test_webserver", "start")
        time.sleep(0.2)  # Give it time to start
        
        self.assertTrue(module.background_task_running)
        
        # Clean up
        self.protocol.send_action("test_webserver", "shutdown")
        module.thread.join(timeout=1.0)

    def test_http_server_serves_index_page(self):
        """Test that the web server serves the index page."""
        module = WebServer("test_webserver", self.protocol, debug=0)
        time.sleep(0.2)

        response = request.urlopen(f"http://{module.host}:{module.port}/", timeout=2)
        body = response.read().decode("utf-8")

        self.assertEqual(response.status, 200)
        self.assertIn("PAF Web Server", body)

        self.protocol.send_action("test_webserver", "shutdown")
        module.thread.join(timeout=1.0)

    def test_http_api_reports_registered_modules(self):
        """Test that the API returns the list of registered modules."""
        module = WebServer("test_webserver", self.protocol, debug=0)
        self.protocol.register_module("extra_module")
        time.sleep(0.2)

        response = request.urlopen(f"http://{module.host}:{module.port}/api/modules", timeout=2)
        payload = json.loads(response.read().decode("utf-8"))

        self.assertIn("test_webserver", payload["modules"])
        self.assertIn("extra_module", payload["modules"])

        self.protocol.send_action("test_webserver", "shutdown")
        module.thread.join(timeout=1.0)

    def test_http_server_serves_static_assets(self):
        """Test that external CSS and JS files are served."""
        module = WebServer("test_webserver", self.protocol, debug=0)
        time.sleep(0.2)

        css_response = request.urlopen(f"http://{module.host}:{module.port}/styles.css", timeout=2)
        js_response = request.urlopen(f"http://{module.host}:{module.port}/app.js", timeout=2)

        self.assertEqual(css_response.status, 200)
        self.assertEqual(js_response.status, 200)
        self.assertIn("--bg", css_response.read().decode("utf-8"))
        self.assertIn("loadModules", js_response.read().decode("utf-8"))

        self.protocol.send_action("test_webserver", "shutdown")
        module.thread.join(timeout=1.0)

    def test_http_api_shutdown_broadcasts_shutdown(self):
        """Test that the shutdown API triggers a protocol broadcast."""
        module = WebServer("test_webserver", self.protocol, debug=0)
        worker = WebServer("worker_webserver", self.protocol, debug=0)
        time.sleep(0.2)

        req = request.Request(
            f"http://{module.host}:{module.port}/api/shutdown",
            data=b"{}",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        response = request.urlopen(req, timeout=2)
        payload = json.loads(response.read().decode("utf-8"))

        self.assertEqual(response.status, 200)
        self.assertTrue(payload["success"])

        module.thread.join(timeout=1.0)
        worker.thread.join(timeout=1.0)
        self.assertFalse(module.thread.is_alive())
        self.assertFalse(worker.thread.is_alive())


if __name__ == '__main__':
    unittest.main()
