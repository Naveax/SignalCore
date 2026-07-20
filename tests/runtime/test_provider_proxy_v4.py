from __future__ import annotations

import http.client
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from signalcore_runtime.evidence import EvidenceStore
from signalcore_runtime.provider_gateway import ProviderGateway
from signalcore_runtime.provider_proxy import ProviderProxyRuntime, ProxyConfig
from signalcore_runtime.usage_receipt_ledger import UsageReceiptLedger


class _UpstreamHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    calls = 0
    last_authorization = ""
    last_payload: dict = {}

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_POST(self) -> None:
        type(self).calls += 1
        type(self).last_authorization = self.headers.get("Authorization", "")
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length))
        type(self).last_payload = payload
        if payload.get("stream"):
            body = b'data: {"delta":"one"}\n\ndata: [DONE]\n\n'
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()
            return
        body = json.dumps({
            "id": "resp-proxy",
            "output_text": "answer",
            "usage": {
                "input_tokens": 12,
                "input_tokens_details": {"cached_tokens": 4},
                "output_tokens": 3,
            },
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class ProviderProxyV4Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        _UpstreamHandler.calls = 0
        _UpstreamHandler.last_authorization = ""
        _UpstreamHandler.last_payload = {}
        self.upstream = ThreadingHTTPServer(("127.0.0.1", 0), _UpstreamHandler)
        self.upstream_thread = threading.Thread(target=self.upstream.serve_forever, daemon=True)
        self.upstream_thread.start()
        upstream_host, upstream_port = self.upstream.server_address

        evidence = EvidenceStore(self.root / "evidence", project_id="proxy-test")
        ledger = UsageReceiptLedger(self.root / "usage.sqlite3", signing_key=b"proxy-test-key")
        gateway = ProviderGateway(self.root / "gateway.sqlite3", evidence=evidence, usage_ledger=ledger)
        self.proxy = ProviderProxyRuntime(
            ProxyConfig(
                provider="openai",
                upstream_base=f"http://{upstream_host}:{upstream_port}",
                listen_port=0,
                credential_env="TEST_PROVIDER_KEY",
                allow_insecure_upstream=True,
                timeout_seconds=5,
            ),
            gateway=gateway,
            insight_path=self.root / "proxy-insights.sqlite3",
        )
        self.env = patch.dict(os.environ, {"TEST_PROVIDER_KEY": "server-secret"}, clear=False)
        self.env.start()
        self.host, self.port = self.proxy.start()

    def tearDown(self):
        self.proxy.shutdown()
        self.upstream.shutdown()
        self.upstream.server_close()
        self.upstream_thread.join(timeout=5)
        self.env.stop()
        self.temp.cleanup()

    def request(self, payload: dict, *, authorization: str = "Bearer client-secret") -> tuple[int, dict[str, str], bytes]:
        connection = http.client.HTTPConnection(self.host, self.port, timeout=5)
        body = json.dumps(payload).encode("utf-8")
        connection.request(
            "POST",
            "/v1/responses",
            body=body,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
                "Authorization": authorization,
            },
        )
        response = connection.getresponse()
        raw = response.read()
        headers = {key: value for key, value in response.getheaders()}
        status = response.status
        connection.close()
        return status, headers, raw

    @staticmethod
    def payload(*, stream: bool = False) -> dict:
        return {
            "model": "gpt-test",
            "messages": [
                {"role": "system", "content": "stable repository context"},
                {"role": "user", "content": "question"},
            ],
            "temperature": 0,
            "stream": stream,
        }

    def test_proxy_injects_server_credential_and_replays_exact_response(self):
        status, headers, raw = self.request(self.payload())
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)["output_text"], "answer")
        self.assertEqual(_UpstreamHandler.last_authorization, "Bearer server-secret")
        self.assertNotEqual(_UpstreamHandler.last_authorization, "Bearer client-secret")
        self.assertIn("prompt_cache_key", _UpstreamHandler.last_payload)
        self.assertEqual(headers["X-SignalCore-Replay"], "miss")
        self.assertTrue(headers["X-SignalCore-Evidence"].startswith("sc://evidence/"))
        self.assertEqual(_UpstreamHandler.calls, 1)

        status, headers, raw = self.request(self.payload())
        self.assertEqual(status, 200)
        self.assertEqual(headers["X-SignalCore-Replay"], "hit")
        self.assertEqual(json.loads(raw)["id"], "resp-proxy")
        self.assertEqual(_UpstreamHandler.calls, 1)
        self.assertTrue(self.proxy.verify()["ok"])

    def test_streaming_is_passed_through_and_not_replayed(self):
        status, headers, raw = self.request(self.payload(stream=True))
        self.assertEqual(status, 200)
        self.assertEqual(raw, b'data: {"delta":"one"}\n\ndata: [DONE]\n\n')
        self.assertEqual(headers["X-SignalCore-Capture"], "stream-deferred")
        self.assertEqual(headers["X-SignalCore-Replay"], "miss")
        status, _, _ = self.request(self.payload(stream=True))
        self.assertEqual(status, 200)
        self.assertEqual(_UpstreamHandler.calls, 2)
        self.assertGreaterEqual(self.proxy.status()["insights"]["events"], 2)

    def test_health_endpoint_and_fixed_origin_reject_absolute_target(self):
        connection = http.client.HTTPConnection(self.host, self.port, timeout=5)
        connection.request("GET", "/_signalcore/health")
        response = connection.getresponse()
        health = json.loads(response.read())
        self.assertEqual(response.status, 200)
        self.assertTrue(health["ok"])
        connection.close()

        connection = http.client.HTTPConnection(self.host, self.port, timeout=5)
        connection.putrequest("POST", "http://attacker.invalid/v1/responses", skip_host=True)
        body = json.dumps(self.payload()).encode("utf-8")
        connection.putheader("Host", "attacker.invalid")
        connection.putheader("Content-Type", "application/json")
        connection.putheader("Content-Length", str(len(body)))
        connection.endheaders(body)
        response = connection.getresponse()
        response.read()
        self.assertEqual(response.status, 502)
        connection.close()
        self.assertEqual(_UpstreamHandler.calls, 0)

    def test_remote_binding_requires_explicit_control_plane_protection(self):
        with self.assertRaises(ValueError):
            ProxyConfig(
                provider="openai",
                upstream_base="https://api.example.invalid",
                listen_host="0.0.0.0",
            ).validate()


if __name__ == "__main__":
    unittest.main()
