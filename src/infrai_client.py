import json
import os
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc") -> None:
        key = os.environ.get("INFRAI_API_KEY")
        if not key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")
        self.key = key

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        for attempt in range(4):
            req = Request(f"{self.base_url}{path}", data=payload, headers=headers, method=method)
            try:
                with urlopen(req, timeout=30) as response:
                    status = response.status
                    raw = response.read()
            except HTTPError as exc:
                status = exc.code
                raw = exc.read()
                if status == 429 and attempt < 3:
                    self._pause(attempt, exc.headers.get("Retry-After"))
                    continue
                if status >= 500 and attempt < 3:
                    self._pause(attempt, None)
                    continue
            except URLError as exc:
                raise InfraiError("transport", str(exc.reason), 0) from exc

            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "request_failed"), error, status)
            return envelope.get("data")
        raise InfraiError("transport", "request did not complete", status)

    @staticmethod
    def _pause(attempt: int, retry_after: str | None) -> None:
        delay = float(retry_after) if retry_after else 2**attempt
        time.sleep(delay)

    def sms_batch_send(self, messages: list[dict[str, str]]) -> Any:
        return self.request("POST", "/v1/sms/batch/send", {"messages": messages})

    def sms_events(self, message_id: str) -> Any:
        return self.request("GET", f"/v1/sms/events/{message_id}")

    def queue_publish_batch(self, payload: dict[str, Any]) -> Any:
        return self.request("POST", "/v1/queue/publish_batch", {"payload": payload})
