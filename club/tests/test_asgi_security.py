import time

from asgiref.sync import async_to_sync
from asgiref.testing import ApplicationCommunicator
from django.test import SimpleTestCase

from club.asgi import application


class AsgiHeaderHandlingSecurityTests(SimpleTestCase):
    def test_repeated_headers_do_not_break_asgi_request_processing(self):
        repeated_headers = [(b"x-repeated", b"value")] * 3000
        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/robots.txt",
            "raw_path": b"/robots.txt",
            "query_string": b"",
            "headers": [(b"host", b"testserver")] + repeated_headers,
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
        }

        communicator = ApplicationCommunicator(application, scope)

        start_time = time.monotonic()
        async_to_sync(communicator.send_input)(
            {"type": "http.request", "body": b"", "more_body": False}
        )

        response_start = async_to_sync(communicator.receive_output)(timeout=2)
        response_body = async_to_sync(communicator.receive_output)(timeout=2)
        elapsed = time.monotonic() - start_time

        self.assertEqual(response_start["type"], "http.response.start")
        self.assertEqual(response_start["status"], 200)
        self.assertEqual(response_body["type"], "http.response.body")
        self.assertFalse(response_body.get("more_body", False))

        # Guardrail against pathological processing of repeated headers.
        self.assertLess(elapsed, 2.0)

        async_to_sync(communicator.wait)()
