from __future__ import annotations

import base64
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ImageGenerator:
    """Generates images using an OpenAI-compatible Images API."""

    def __init__(self, images_dir: Path) -> None:
        self.images_dir = images_dir
        self.images_dir.mkdir(parents=True, exist_ok=True)

        self.api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        self.base_url = (os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.model = (os.getenv("OPENAI_IMAGE_MODEL") or "gpt-image-1").strip()
        self.size = (os.getenv("OPENAI_IMAGE_SIZE") or "1024x1024").strip()
        self.timeout = self._read_int_env("OPENAI_TIMEOUT_SECONDS", default=120)

    def generate_image(self, saying_id: int, prompt: str) -> Path:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is missing. Set it before generating images.")

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"saying_{saying_id}_{timestamp}.png"
        output = self.images_dir / filename

        image_bytes = self._generate_via_api(prompt=prompt)
        output.write_bytes(image_bytes)
        return output

    def _generate_via_api(self, prompt: str) -> bytes:
        endpoint = f"{self.base_url}/images/generations"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "size": self.size,
            "n": 1,
        }

        req = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(req, timeout=self.timeout) as response:
                body = response.read()
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Image API request failed ({exc.code}): {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Image API connection failed: {exc.reason}") from exc

        try:
            parsed = json.loads(body.decode("utf-8"))
            item = parsed["data"][0]
        except Exception as exc:
            raise RuntimeError("Image API returned invalid JSON payload.") from exc

        if "b64_json" in item and item["b64_json"]:
            try:
                return base64.b64decode(item["b64_json"])
            except Exception as exc:
                raise RuntimeError("Image API returned invalid base64 image payload.") from exc

        if "url" in item and item["url"]:
            try:
                with urlopen(item["url"], timeout=self.timeout) as image_response:
                    return image_response.read()
            except Exception as exc:
                raise RuntimeError("Image API returned URL but image download failed.") from exc

        raise RuntimeError("Image API response contained no image data.")

    @staticmethod
    def _read_int_env(name: str, default: int) -> int:
        raw = os.getenv(name)
        if raw is None:
            return default
        raw = raw.strip()
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError:
            return default
