"""MONAI Label REST client wrapper for TumorLens AI."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Callable
from urllib import error, request
from uuid import uuid4


Transport = Callable[[str, str, dict[str, str], bytes | None, float], tuple[int, Any]]


@dataclass
class ServerStatus:
    url: str
    reachable: bool
    models: list[str]
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TumorLensAIMONAIClient:
    """Small, testable client for a separately running MONAI Label server."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 10.0, transport: Transport | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._transport = transport or self._urllib_transport

    def check_status(self) -> ServerStatus:
        try:
            info = self.get_info()
            models = self.get_models(info)
            return ServerStatus(
                url=self.base_url,
                reachable=True,
                models=models,
                message="MONAI Label server is reachable.",
            )
        except Exception as exc:  # noqa: BLE001 - surfaced as a status object for UI/workflow callers.
            return ServerStatus(
                url=self.base_url,
                reachable=False,
                models=[],
                message=str(exc),
            )

    def get_info(self) -> dict[str, Any]:
        status_code, payload = self._json_request("GET", "/info")
        if status_code == 404:
            status_code, payload = self._json_request("GET", "/")
        if status_code >= 400:
            raise RuntimeError(f"MONAI Label info request failed with HTTP {status_code}.")
        return payload if isinstance(payload, dict) else {"response": payload}

    def get_models(self, info_payload: dict[str, Any] | None = None) -> list[str]:
        try:
            status_code, payload = self._json_request("GET", "/models")
            if status_code < 400:
                return self._extract_models(payload)
        except Exception:
            pass

        if info_payload:
            return self._extract_models(info_payload)
        return []

    def run_inference_file(self, model_name: str, image_path: str | Path) -> dict[str, Any]:
        """Run model inference by posting an image file.

        MONAI Label deployments vary in how they expose file uploads, so this
        method targets the common `/infer/{model}` shape and returns the raw
        response for the Slicer logic to interpret.
        """

        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Input image does not exist: {image_path}")

        url = f"{self.base_url}/infer/{model_name}"
        body, content_type = self._multipart_file_body("file", image_path)
        status_code, payload = self._transport(
            "POST",
            url,
            {"Content-Type": content_type},
            body,
            self.timeout,
        )
        if status_code >= 400:
            raise RuntimeError(f"MONAI Label inference failed with HTTP {status_code}.")
        return payload if isinstance(payload, dict) else {"response": payload}

    def _json_request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"}
        return self._transport(method, f"{self.base_url}{path}", headers, body, self.timeout)

    def _urllib_transport(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: bytes | None,
        timeout: float,
    ) -> tuple[int, Any]:
        req = request.Request(url, data=body, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=timeout) as response:  # noqa: S310 - user-provided local MONAI endpoint.
                raw = response.read().decode("utf-8")
                return response.status, json.loads(raw) if raw else {}
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            payload = json.loads(raw) if raw else {}
            return exc.code, payload

    def _extract_models(self, payload: Any) -> list[str]:
        if isinstance(payload, list):
            return [str(item) for item in payload]

        if not isinstance(payload, dict):
            return []

        for key in ("models", "model", "infer", "inference"):
            value = payload.get(key)
            if isinstance(value, list):
                return [str(item) for item in value]
            if isinstance(value, dict):
                return [str(item) for item in value.keys()]

        nested = payload.get("config")
        if isinstance(nested, dict):
            return self._extract_models(nested)

        return []

    def _multipart_file_body(self, field_name: str, path: Path) -> tuple[bytes, str]:
        boundary = f"tumorlensai-{uuid4().hex}"
        content_type = f"multipart/form-data; boundary={boundary}"
        file_bytes = path.read_bytes()
        header = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field_name}"; filename="{path.name}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8")
        footer = f"\r\n--{boundary}--\r\n".encode("utf-8")
        return header + file_bytes + footer, content_type
