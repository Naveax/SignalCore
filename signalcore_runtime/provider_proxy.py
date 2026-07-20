from __future__ import annotations

import json
import os
import secrets
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

from .competitive_fabric import InsightLedger
from .provider_gateway import ProviderGateway, ProviderPlan
from .security_scan import scan_text
from .util import canonical_json, sha256_bytes


_HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailer", "transfer-encoding", "upgrade", "host", "content-length",
}
_CREDENTIAL_HEADERS = {
    "authorization", "x-api-key", "api-key", "x-goog-api-key",
}
_FORWARD_HEADERS = {
    "accept", "content-type", "user-agent", "openai-beta", "openai-organization",
    "openai-project", "anthropic-version", "anthropic-beta", "x-goog-user-project",
    "x-request-id", "traceparent", "tracestate",
}
_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}


@dataclass(frozen=True)
class ProxyConfig:
    provider: str
    upstream_base: str
    listen_host: str = "127.0.0.1"
    listen_port: int = 8787
    credential_env: str = ""
    credential_header: str = ""
    credential_prefix: str = ""
    control_token_env: str = "SIGNALCORE_PROXY_CONTROL_TOKEN"
    allow_remote: bool = False
    allow_insecure_upstream: bool = False
    cache_policy: str = "auto"
    replay_ttl_seconds: int = 900
    prompt_cache_ttl_seconds: int = 300
    timeout_seconds: float = 180.0
    max_request_bytes: int = 16 * 1024 * 1024
    max_buffered_response_bytes: int = 64 * 1024 * 1024
    spool_memory_bytes: int = 2 * 1024 * 1024
    default_anthropic_version: str = "2023-06-01"

    def validate(self) -> None:
        if self.listen_port < 0 or self.listen_port > 65535:
            raise ValueError("listen_port must be between 0 and 65535")
        if self.max_request_bytes < 1024:
            raise ValueError("max_request_bytes must be at least 1024")
        if self.max_buffered_response_bytes < 1024:
            raise ValueError("max_buffered_response_bytes must be at least 1024")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.cache_policy not in {"off", "auto", "read", "read-write"}:
            raise ValueError("invalid cache_policy")
        parsed = urllib.parse.urlsplit(self.upstream_base)
        if parsed.scheme not in ({"http", "https"} if self.allow_insecure_upstream else {"https"}):
            raise ValueError("upstream must use HTTPS unless allow_insecure_upstream is explicit")
        if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("upstream_base must be an origin or fixed base path without credentials/query/fragment")
        if self.listen_host not in _LOOPBACK_HOSTS:
            if not self.allow_remote:
                raise ValueError("non-loopback proxy binding requires allow_remote")
            if not self.control_token_env:
                raise ValueError("remote proxy binding requires a control token environment variable")


@dataclass(frozen=True)
class RawTransportCapture:
    provider: str
    model: str
    request_hash: str
    status_code: int
    content_type: str
    transport_hash: str
    transport_handle: str
    bytes: int
    visible_preview: str
    secret_types: tuple[str, ...]
    injection_risk: bool


@dataclass(frozen=True)
class ProxyResult:
    status_code: int
    replay_hit: bool
    request_handle: str
    response_handle: str
    response_hash: str
    bytes_sent: int
    duration_ms: float
    streaming: bool


class ProviderProxyRuntime:
    """Credential-isolated reverse proxy over ProviderGateway.

    The client never chooses the upstream origin. The configured fixed origin prevents
    SSRF. Incoming credential headers are discarded and credentials are injected only
    from an environment variable. Non-streaming deterministic responses may be replayed;
    streaming responses are passed through and captured byte-for-byte after completion.
    """

    def __init__(self, config: ProxyConfig, *, gateway: ProviderGateway, insight_path: Path):
        config.validate()
        self.config = config
        self.gateway = gateway
        self.insights = InsightLedger(insight_path)
        self._lock = threading.RLock()
        self._active = 0
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def address(self) -> tuple[str, int]:
        if self._server is None:
            return self.config.listen_host, self.config.listen_port
        host, port = self._server.server_address[:2]
        return str(host), int(port)

    @staticmethod
    def _provider_defaults(provider: str) -> tuple[str, str]:
        canonical = ProviderGateway.capabilities(provider)["provider"]
        if canonical == "openai":
            return "Authorization", "Bearer "
        if canonical == "anthropic":
            return "x-api-key", ""
        if canonical == "gemini":
            return "x-goog-api-key", ""
        return "Authorization", "Bearer "

    def _credential(self) -> tuple[str, str] | None:
        if not self.config.credential_env:
            return None
        value = os.environ.get(self.config.credential_env, "")
        if not value:
            raise RuntimeError(f"missing provider credential environment variable: {self.config.credential_env}")
        default_header, default_prefix = self._provider_defaults(self.config.provider)
        return (
            self.config.credential_header or default_header,
            (self.config.credential_prefix if self.config.credential_prefix else default_prefix) + value,
        )

    def _upstream_url(self, raw_target: str) -> str:
        parsed_target = urllib.parse.urlsplit(raw_target)
        if parsed_target.scheme or parsed_target.netloc:
            raise ValueError("absolute proxy targets are forbidden")
        if not parsed_target.path.startswith("/"):
            raise ValueError("request target must be origin-form")
        base = urllib.parse.urlsplit(self.config.upstream_base)
        base_path = base.path.rstrip("/")
        path = parsed_target.path
        joined_path = f"{base_path}{path}" if base_path else path
        return urllib.parse.urlunsplit((base.scheme, base.netloc, joined_path, parsed_target.query, ""))

    def _headers(self, incoming: Mapping[str, str], body_length: int) -> dict[str, str]:
        result: dict[str, str] = {}
        for key, value in incoming.items():
            name = key.casefold()
            if name in _HOP_BY_HOP or name in _CREDENTIAL_HEADERS:
                continue
            if name in _FORWARD_HEADERS or name.startswith("x-signalcore-client-"):
                result[key] = value
        result["Content-Length"] = str(body_length)
        result.setdefault("Content-Type", "application/json")
        canonical = ProviderGateway.capabilities(self.config.provider)["provider"]
        if canonical == "anthropic":
            result.setdefault("anthropic-version", self.config.default_anthropic_version)
        credential = self._credential()
        if credential:
            result[credential[0]] = credential[1]
        return result

    def _raw_capture(
        self,
        plan: ProviderPlan,
        body: bytes,
        *,
        status_code: int,
        content_type: str,
        response_headers: Mapping[str, str],
    ) -> RawTransportCapture:
        transport_hash = sha256_bytes(body)
        handle = self.gateway.evidence.put(
            body,
            kind="provider-response-transport",
            metadata={
                "provider": plan.provider,
                "model": plan.model,
                "request_hash": plan.request_hash,
                "transport_hash": transport_hash,
                "status_code": int(status_code),
                "content_type": content_type,
                "response_headers": {
                    key: value for key, value in response_headers.items()
                    if key.casefold() not in _HOP_BY_HOP and key.casefold() not in _CREDENTIAL_HEADERS
                },
            },
        )
        decoded = body.decode("utf-8", errors="replace")
        security = scan_text(decoded)
        preview_raw = security.redacted_text.encode("utf-8")
        marker = "\n[… exact provider transport stored as evidence …]"
        if len(preview_raw) > 4096:
            keep = max(0, 4096 - len(marker.encode("utf-8")))
            preview = preview_raw[:keep].decode("utf-8", errors="ignore").rstrip() + marker
        else:
            preview = security.redacted_text
        return RawTransportCapture(
            provider=plan.provider,
            model=plan.model,
            request_hash=plan.request_hash,
            status_code=int(status_code),
            content_type=content_type,
            transport_hash=transport_hash,
            transport_handle=handle,
            bytes=len(body),
            visible_preview=preview,
            secret_types=security.secret_types,
            injection_risk=security.injection_risk,
        )

    def _prepare(self, payload: Mapping[str, Any]) -> ProviderPlan:
        return self.gateway.prepare(
            self.config.provider,
            payload,
            model=str(payload.get("model") or ""),
            cache_policy=self.config.cache_policy,
            replay_ttl_seconds=self.config.replay_ttl_seconds,
            prompt_cache_ttl_seconds=self.config.prompt_cache_ttl_seconds,
        )

    def _enter(self) -> None:
        with self._lock:
            self._active += 1

    def _exit(self) -> None:
        with self._lock:
            self._active = max(0, self._active - 1)

    def status(self) -> dict[str, Any]:
        with self._lock:
            active = self._active
        return {
            "ok": True,
            "provider": ProviderGateway.capabilities(self.config.provider)["provider"],
            "listen": {"host": self.address[0], "port": self.address[1]},
            "upstream_origin_hash": sha256_bytes(self.config.upstream_base.encode("utf-8")),
            "cache_policy": self.config.cache_policy,
            "active_requests": active,
            "gateway": self.gateway.stats(),
            "insights": self.insights.metrics(),
        }

    def verify(self) -> dict[str, Any]:
        gateway = self.gateway.verify()
        insights_ok = self.insights.state.integrity_check()
        return {
            "ok": bool(gateway["ok"] and insights_ok),
            "gateway": gateway,
            "insights_database_integrity": insights_ok,
        }

    def _control_allowed(self, headers: Mapping[str, str]) -> bool:
        if self.config.listen_host in _LOOPBACK_HOSTS:
            return True
        expected = os.environ.get(self.config.control_token_env, "")
        supplied = headers.get("Authorization", "")
        return bool(expected) and secrets.compare_digest(supplied, f"Bearer {expected}")

    def _handler_type(self) -> type[BaseHTTPRequestHandler]:
        runtime = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"
            server_version = "SignalCoreProviderProxy/0.4"

            def log_message(self, format: str, *args: Any) -> None:
                # Never emit request headers or provider bodies through stdlib logging.
                return

            def _json(self, status: int, payload: Mapping[str, Any], headers: Mapping[str, str] | None = None) -> None:
                body = canonical_json(dict(payload))
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                for key, value in (headers or {}).items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(body)

            def _control(self) -> bool:
                if runtime._control_allowed(self.headers):
                    return True
                self._json(HTTPStatus.UNAUTHORIZED, {"error": "invalid-control-token"})
                return False

            def do_GET(self) -> None:
                target = urllib.parse.urlsplit(self.path).path
                if target == "/_signalcore/health":
                    if self._control():
                        self._json(HTTPStatus.OK, runtime.status())
                    return
                if target == "/_signalcore/verify":
                    if self._control():
                        result = runtime.verify()
                        self._json(HTTPStatus.OK if result["ok"] else HTTPStatus.CONFLICT, result)
                    return
                self._proxy_without_json_body("GET")

            def do_POST(self) -> None:
                runtime._enter()
                started = time.perf_counter()
                try:
                    self._post(started)
                finally:
                    runtime._exit()

            def _post(self, started: float) -> None:
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid-content-length"})
                    return
                if length <= 0:
                    self._json(HTTPStatus.BAD_REQUEST, {"error": "json-body-required"})
                    return
                if length > runtime.config.max_request_bytes:
                    self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "request-body-too-large"})
                    return
                raw_request = self.rfile.read(length)
                try:
                    payload = json.loads(raw_request)
                except json.JSONDecodeError as exc:
                    self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid-json", "detail": str(exc)})
                    return
                if not isinstance(payload, Mapping):
                    self._json(HTTPStatus.BAD_REQUEST, {"error": "provider-request-must-be-object"})
                    return
                try:
                    plan = runtime._prepare(payload)
                except Exception as exc:
                    self._json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__, "detail": str(exc)})
                    return
                streaming = bool(plan.prepared_request.get("stream") or plan.prepared_request.get("streaming"))
                if plan.replay_hit and not streaming:
                    replay = runtime.gateway.replay(plan)
                    if replay is not None:
                        body = canonical_json(replay)
                        self.send_response(HTTPStatus.OK)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(body)))
                        self.send_header("X-SignalCore-Replay", "hit")
                        self.send_header("X-SignalCore-Request-Handle", plan.request_handle)
                        self.end_headers()
                        self.wfile.write(body)
                        duration = (time.perf_counter() - started) * 1000
                        runtime.insights.record(
                            "provider-proxy", family=plan.provider, host="proxy",
                            raw_bytes=len(body), visible_bytes=len(body), latency_ms=duration,
                            success=True, cache_hit=True,
                            metadata={"status": 200, "streaming": False},
                        )
                        return
                prepared_body = canonical_json(plan.prepared_request)
                try:
                    url = runtime._upstream_url(self.path)
                    request = urllib.request.Request(
                        url,
                        data=prepared_body,
                        headers=runtime._headers(self.headers, len(prepared_body)),
                        method="POST",
                    )
                    try:
                        response = urllib.request.urlopen(request, timeout=runtime.config.timeout_seconds)
                    except urllib.error.HTTPError as exc:
                        response = exc
                    status = int(response.status)
                    response_headers = {str(key): str(value) for key, value in response.headers.items()}
                    content_type = response.headers.get("Content-Type", "application/octet-stream")
                    if streaming:
                        self._stream_response(
                            response, plan, status, response_headers, content_type, started
                        )
                    else:
                        self._buffer_response(
                            response, plan, status, response_headers, content_type, started
                        )
                except (urllib.error.URLError, TimeoutError, ValueError, RuntimeError) as exc:
                    duration = (time.perf_counter() - started) * 1000
                    runtime.insights.record(
                        "provider-proxy", family=plan.provider, host="proxy",
                        latency_ms=duration, success=False,
                        metadata={"error": type(exc).__name__},
                    )
                    self._json(HTTPStatus.BAD_GATEWAY, {"error": type(exc).__name__, "detail": str(exc)})

            def _forward_response_headers(
                self,
                status: int,
                headers: Mapping[str, str],
                *,
                content_length: int | None,
                plan: ProviderPlan,
                evidence_handle: str = "",
                streaming: bool = False,
            ) -> None:
                self.send_response(status)
                for key, value in headers.items():
                    name = key.casefold()
                    if name in _HOP_BY_HOP or name in _CREDENTIAL_HEADERS or name == "content-length":
                        continue
                    self.send_header(key, value)
                if content_length is not None:
                    self.send_header("Content-Length", str(content_length))
                else:
                    self.send_header("Connection", "close")
                    self.close_connection = True
                self.send_header("X-SignalCore-Replay", "miss")
                self.send_header("X-SignalCore-Request-Handle", plan.request_handle)
                self.send_header("X-SignalCore-Capture", "stream-deferred" if streaming else "complete")
                if evidence_handle:
                    self.send_header("X-SignalCore-Evidence", evidence_handle)
                self.end_headers()

            def _buffer_response(
                self,
                response: Any,
                plan: ProviderPlan,
                status: int,
                response_headers: Mapping[str, str],
                content_type: str,
                started: float,
            ) -> None:
                body = response.read(runtime.config.max_buffered_response_bytes + 1)
                if len(body) > runtime.config.max_buffered_response_bytes:
                    self._json(HTTPStatus.BAD_GATEWAY, {"error": "upstream-response-too-large-for-buffered-mode"})
                    return
                raw_capture = runtime._raw_capture(
                    plan, body, status_code=status, content_type=content_type,
                    response_headers=response_headers,
                )
                semantic_handle = ""
                if "json" in content_type.casefold():
                    try:
                        decoded = json.loads(body)
                    except json.JSONDecodeError:
                        decoded = None
                    if isinstance(decoded, Mapping):
                        semantic = runtime.gateway.capture(
                            plan,
                            decoded,
                            store_replay=200 <= status < 300,
                            replay_ttl_seconds=runtime.config.replay_ttl_seconds,
                        )
                        semantic_handle = semantic.response_handle
                self._forward_response_headers(
                    status,
                    response_headers,
                    content_length=len(body),
                    plan=plan,
                    evidence_handle=raw_capture.transport_handle,
                )
                self.wfile.write(body)
                duration = (time.perf_counter() - started) * 1000
                runtime.insights.record(
                    "provider-proxy", family=plan.provider, host="proxy",
                    raw_bytes=len(body), visible_bytes=len(raw_capture.visible_preview.encode("utf-8")),
                    latency_ms=duration, success=200 <= status < 500,
                    cache_hit=False,
                    metadata={
                        "status": status,
                        "streaming": False,
                        "transport_handle": raw_capture.transport_handle,
                        "semantic_handle": semantic_handle,
                    },
                )

            def _stream_response(
                self,
                response: Any,
                plan: ProviderPlan,
                status: int,
                response_headers: Mapping[str, str],
                content_type: str,
                started: float,
            ) -> None:
                self._forward_response_headers(
                    status,
                    response_headers,
                    content_length=None,
                    plan=plan,
                    streaming=True,
                )
                total = 0
                with tempfile.SpooledTemporaryFile(max_size=runtime.config.spool_memory_bytes) as spool:
                    while True:
                        chunk = response.read(64 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > runtime.config.max_buffered_response_bytes:
                            raise RuntimeError("stream capture exceeded configured maximum")
                        spool.write(chunk)
                        self.wfile.write(chunk)
                        self.wfile.flush()
                    spool.seek(0)
                    body = spool.read()
                raw_capture = runtime._raw_capture(
                    plan, body, status_code=status, content_type=content_type,
                    response_headers=response_headers,
                )
                duration = (time.perf_counter() - started) * 1000
                runtime.insights.record(
                    "provider-proxy", family=plan.provider, host="proxy",
                    raw_bytes=total, visible_bytes=len(raw_capture.visible_preview.encode("utf-8")),
                    latency_ms=duration, success=200 <= status < 500,
                    cache_hit=False,
                    metadata={
                        "status": status,
                        "streaming": True,
                        "transport_handle": raw_capture.transport_handle,
                    },
                )

            def _proxy_without_json_body(self, method: str) -> None:
                started = time.perf_counter()
                try:
                    url = runtime._upstream_url(self.path)
                    headers = runtime._headers(self.headers, 0)
                    headers.pop("Content-Length", None)
                    request = urllib.request.Request(url, headers=headers, method=method)
                    try:
                        response = urllib.request.urlopen(request, timeout=runtime.config.timeout_seconds)
                    except urllib.error.HTTPError as exc:
                        response = exc
                    body = response.read(runtime.config.max_buffered_response_bytes + 1)
                    if len(body) > runtime.config.max_buffered_response_bytes:
                        self._json(HTTPStatus.BAD_GATEWAY, {"error": "upstream-response-too-large"})
                        return
                    status = int(response.status)
                    self.send_response(status)
                    for key, value in response.headers.items():
                        if key.casefold() not in _HOP_BY_HOP and key.casefold() not in _CREDENTIAL_HEADERS and key.casefold() != "content-length":
                            self.send_header(key, value)
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("X-SignalCore-Capture", "passthrough")
                    self.end_headers()
                    self.wfile.write(body)
                    runtime.insights.record(
                        "provider-proxy", family="passthrough", host="proxy",
                        raw_bytes=len(body), visible_bytes=len(body),
                        latency_ms=(time.perf_counter() - started) * 1000,
                        success=200 <= status < 500,
                        metadata={"status": status, "method": method},
                    )
                except Exception as exc:
                    self._json(HTTPStatus.BAD_GATEWAY, {"error": type(exc).__name__, "detail": str(exc)})

        return Handler

    def start(self) -> tuple[str, int]:
        if self._server is not None:
            return self.address
        self._server = ThreadingHTTPServer(
            (self.config.listen_host, self.config.listen_port),
            self._handler_type(),
        )
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="signalcore-provider-proxy",
            daemon=True,
        )
        self._thread.start()
        return self.address

    def serve_forever(self) -> None:
        if self._server is not None:
            raise RuntimeError("proxy already started")
        self._server = ThreadingHTTPServer(
            (self.config.listen_host, self.config.listen_port),
            self._handler_type(),
        )
        try:
            self._server.serve_forever()
        finally:
            self._server.server_close()
            self._server = None

    def shutdown(self) -> None:
        server = self._server
        thread = self._thread
        if server is None:
            return
        server.shutdown()
        server.server_close()
        self._server = None
        if thread is not None:
            thread.join(timeout=5)
        self._thread = None
