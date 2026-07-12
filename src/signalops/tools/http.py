from __future__ import annotations

import socket
import urllib.error
import urllib.request
from dataclasses import dataclass

from signalops.framework import StepError, retry_call


@dataclass
class HttpResponse:
    url: str
    status_code: int
    text: str


class HttpClient:
    def __init__(self, timeout_seconds: float = 6.0, retries: int = 2):
        self.timeout_seconds = timeout_seconds
        self.retries = retries

    def get_text(self, url: str, max_bytes: int = 200_000) -> HttpResponse:
        def operation() -> HttpResponse:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "PerkSignalOpsDemo/0.1"},
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    body = response.read(max_bytes).decode("utf-8", errors="ignore")
                    return HttpResponse(url=url, status_code=response.status, text=body)
            except socket.timeout as exc:
                raise TimeoutError(f"timeout fetching {url}") from exc
            except urllib.error.URLError as exc:
                raise ConnectionError(f"network error fetching {url}: {exc}") from exc
            except Exception as exc:
                raise StepError(f"unexpected http error fetching {url}: {exc}") from exc

        return retry_call(operation, retries=self.retries)
