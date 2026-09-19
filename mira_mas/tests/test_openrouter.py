import os
import tempfile
import unittest
from io import BytesIO
from mira_mas.backends.openrouter import OpenRouterChat, OpenRouterConfig, OpenRouterError
from mira_mas.victims.api_reproductions import _bundle_text


class OpenRouterTests(unittest.TestCase):
    def test_public_config_never_exposes_key(self):
        config = OpenRouterConfig("secret-key", "provider/model")
        self.assertNotIn("secret-key", str(config.public_config()))

    def test_timeout_is_part_of_safe_reproducibility_config(self):
        config = OpenRouterConfig("secret-key", "provider/model", timeout_seconds=30)
        self.assertEqual(config.public_config()["timeout_seconds"], 30)

    def test_json_mode_is_opt_in(self):
        self.assertFalse(OpenRouterConfig("secret-key", "provider/model").supports_json_mode)

    def test_sse_reader_ignores_keep_alive_and_collects_content(self):
        stream = BytesIO(
            b": OPENROUTER PROCESSING\n\n"
            b'data: {"choices":[{"delta":{"content":"review "}}]}\n\n'
            b'data: {"choices":[{"delta":{"content":"complete"}}]}\n\n'
            b"data: [DONE]\n\n"
        )
        self.assertEqual(OpenRouterChat._read_sse(stream), "review complete")

    def test_env_parses_inference_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            dotenv = os.path.join(directory, ".env")
            with open(dotenv, "w", encoding="utf-8") as handle:
                handle.write("""OPENROUTER_API_KEY=test-key
OPENROUTER_MODEL=provider/model
OPENROUTER_TIMEOUT_SECONDS=90
OPENROUTER_MAX_TOKENS=1024
OPENROUTER_TEMPERATURE=0.25
OPENROUTER_REASONING_EFFORT=minimal
""")
            old_key, old_model = os.environ.pop("OPENROUTER_API_KEY", None), os.environ.pop("OPENROUTER_MODEL", None)
            try:
                config = OpenRouterConfig.from_env(dotenv)
            finally:
                if old_key is not None:
                    os.environ["OPENROUTER_API_KEY"] = old_key
                if old_model is not None:
                    os.environ["OPENROUTER_MODEL"] = old_model
        self.assertEqual((config.timeout_seconds, config.max_tokens, config.temperature, config.reasoning_effort),
                         (90.0, 1024, 0.25, "minimal"))

    def test_bundle_requires_immutable_protocol_fields(self):
        with self.assertRaises(ValueError):
            _bundle_text({"diff": "x"})

    def test_no_credentials_fails_before_network(self):
        old_key, old_model = os.environ.pop("OPENROUTER_API_KEY", None), os.environ.pop("OPENROUTER_MODEL", None)
        try:
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(OpenRouterError):
                    OpenRouterConfig.from_env(os.path.join(directory, "missing.env"))
        finally:
            if old_key is not None:
                os.environ["OPENROUTER_API_KEY"] = old_key
            if old_model is not None:
                os.environ["OPENROUTER_MODEL"] = old_model
