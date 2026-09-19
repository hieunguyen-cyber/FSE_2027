"""Small dependency-free client for OpenRouter's OpenAI-compatible chat endpoint."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from mira_mas.backends.cost import CostMeter


class OpenRouterError(RuntimeError):
    pass


@dataclass(frozen=True)
class OpenRouterConfig:
    api_key: str
    model: str
    # Free routes may remain queued for tens of seconds before emitting a token.
    # This is deliberately longer than a typical HTTP health-check timeout.
    timeout_seconds: float = 90.0
    temperature: float = 0.0
    max_tokens: int = 1024
    reasoning_effort: str | None = None
    referer: str | None = None
    app_title: str = "MIRA-MAS"
    supports_json_mode: bool = False
    prompt_price_usd: float = 0.00000015
    completion_price_usd: float = 0.0000006

    @classmethod
    def from_env(cls, dotenv_path: str | Path = ".env") -> "OpenRouterConfig":
        """Read environment first, then an optional local .env without overriding shell values."""
        values = dict(os.environ)
        path = Path(dotenv_path)
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                values.setdefault(name.strip(), value.strip().strip("\"'") )
        key, model = values.get("OPENROUTER_API_KEY"), values.get("OPENROUTER_MODEL")
        if not key or not model:
            raise OpenRouterError("Set OPENROUTER_API_KEY and OPENROUTER_MODEL; no key is read from source files.")
        try:
            timeout = float(values.get("OPENROUTER_TIMEOUT_SECONDS", "90"))
        except ValueError as error:
            raise OpenRouterError("OPENROUTER_TIMEOUT_SECONDS must be numeric") from error
        if timeout <= 0:
            raise OpenRouterError("OPENROUTER_TIMEOUT_SECONDS must be positive")
        try:
            max_tokens = int(values.get("OPENROUTER_MAX_TOKENS", "1024"))
        except ValueError as error:
            raise OpenRouterError("OPENROUTER_MAX_TOKENS must be an integer") from error
        if max_tokens <= 0:
            raise OpenRouterError("OPENROUTER_MAX_TOKENS must be positive")
        try:
            temperature = float(values.get("OPENROUTER_TEMPERATURE", "0"))
        except ValueError as error:
            raise OpenRouterError("OPENROUTER_TEMPERATURE must be numeric") from error
        if not 0 <= temperature <= 2:
            raise OpenRouterError("OPENROUTER_TEMPERATURE must be between 0 and 2")
        reasoning_effort = values.get("OPENROUTER_REASONING_EFFORT", "").strip().lower() or None
        json_mode = values.get("OPENROUTER_JSON_MODE", "false").strip().lower() in {"1", "true", "yes"}
        return cls(key, model, timeout_seconds=timeout, max_tokens=max_tokens, temperature=temperature,
                   reasoning_effort=reasoning_effort,
                   referer=values.get("OPENROUTER_HTTP_REFERER"),
                   app_title=values.get("OPENROUTER_APP_TITLE", "MIRA-MAS"), supports_json_mode=json_mode)

    def public_config(self) -> dict[str, Any]:
        """Safe for a hash manifest; deliberately excludes API credentials."""
        return {"provider": "openrouter", "model": self.model, "temperature": self.temperature,
                "max_tokens": self.max_tokens, "timeout_seconds": self.timeout_seconds,
                "reasoning_effort": self.reasoning_effort, "app_title": self.app_title,
                "supports_json_mode": self.supports_json_mode}


class OpenRouterChat:
    endpoint = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, config: OpenRouterConfig, meter: CostMeter | None = None) -> None:
        self.config = config
        self.meter = meter

    def complete(self, *, system: str, user: str, response_format: dict[str, str] | None = None) -> str:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            # Free routes can queue for longer than an ordinary request timeout.
            # OpenRouter sends SSE keep-alives while queued; consuming the stream
            # prevents a valid, live request from being mistaken for a dead socket.
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if response_format and self.config.supports_json_mode:
            payload["response_format"] = response_format
        if self.config.reasoning_effort:
            payload["reasoning_effort"] = self.config.reasoning_effort
        headers = {"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json",
                   "X-Title": self.config.app_title}
        if self.config.referer:
            headers["HTTP-Referer"] = self.config.referer
        return self._post(payload, headers, retry_without_schema=bool(response_format))

    def _post(self, payload: dict[str, Any], headers: dict[str, str], retry_without_schema: bool) -> str:
        request = Request(self.endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                if "text/event-stream" in response.headers.get("Content-Type", ""):
                    return self._read_sse(response, self.meter, self.config.prompt_price_usd,
                                          self.config.completion_price_usd)
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            # Never include request headers (and therefore the API key) in exceptions or the audit ledger.
            detail = error.read().decode("utf-8", errors="replace")[:500]
            # Some free providers reject OpenAI JSON mode. Retry once with the
            # schema written into the prompt instead of failing the whole run.
            if retry_without_schema and error.code in {400, 404, 422}:
                retry_payload = dict(payload)
                retry_payload.pop("response_format", None)
                return self._post(retry_payload, headers, retry_without_schema=False)
            raise OpenRouterError(f"OpenRouter HTTP {error.code}: {detail}") from error
        except (URLError, TimeoutError, OSError) as error:
            raise OpenRouterError(f"OpenRouter connection failed: {getattr(error, 'reason', str(error))}") from error
        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise OpenRouterError("OpenRouter returned no assistant message") from error

    @staticmethod
    @staticmethod
    def _read_sse(response: Any, meter: CostMeter | None = None,
                  prompt_price: float = 0.00000015, completion_price: float = 0.0000006) -> str:
        """Collect OpenAI-compatible SSE token deltas, ignoring keep-alive comments."""
        chunks: list[str] = []
        usage: dict[str, int] | None = None
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"):
                continue
            event = line[5:].strip()
            if event == "[DONE]":
                break
            try:
                payload = json.loads(event)
                if payload.get("usage"):
                    usage = payload["usage"]
                delta = payload["choices"][0].get("delta", {})
                content = delta.get("content")
            except (json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
                raise OpenRouterError("OpenRouter returned an invalid streaming event") from error
            if isinstance(content, str):
                chunks.append(content)
        content = "".join(chunks)
        if not content:
            raise OpenRouterError("OpenRouter returned no assistant message")
        if meter is not None and usage:
            meter.record(int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0)),
                         prompt_price, completion_price)
        return content
