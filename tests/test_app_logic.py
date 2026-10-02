import base64
from io import BytesIO
import unittest
from unittest.mock import patch

import requests

from app_logic import (
    MAX_INPUT_CHARACTERS,
    MAX_REQUESTS_PER_WINDOW,
    REQUEST_COOLDOWN_SECONDS,
    REQUEST_WINDOW_SECONDS,
    TTS_TIMEOUT,
    TRANSLATION_TIMEOUT,
    create_audio_bytes,
    record_request,
    seconds_until_allowed,
    translate_text,
    validate_input,
)


class FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text
        self.status_checked = False

    def raise_for_status(self) -> None:
        self.status_checked = True


class AppLogicTests(unittest.TestCase):
    def test_validate_input_trims_and_limits_unicode_characters(self) -> None:
        text = " 🙂 "
        self.assertEqual(validate_input(text), "🙂")
        self.assertEqual(validate_input("🙂" * MAX_INPUT_CHARACTERS), "🙂" * MAX_INPUT_CHARACTERS)
        with self.assertRaises(ValueError):
            validate_input("🙂" * (MAX_INPUT_CHARACTERS + 1))
        with self.assertRaises(ValueError):
            validate_input("  \n")

    def test_session_rate_limit_applies_cooldown_and_rolling_window(self) -> None:
        self.assertEqual(seconds_until_allowed(0, []), 0)
        timestamps: list[float] = []
        for attempt in range(MAX_REQUESTS_PER_WINDOW):
            now = float(attempt * REQUEST_COOLDOWN_SECONDS)
            self.assertEqual(seconds_until_allowed(now, timestamps), 0)
            timestamps = record_request(now, timestamps)

        self.assertEqual(
            seconds_until_allowed(25, timestamps),
            REQUEST_WINDOW_SECONDS - 25,
        )
        self.assertEqual(seconds_until_allowed(60, timestamps), 0)
        self.assertEqual(record_request(60, timestamps), [10.0, 20.0, 60])

    def test_translation_uses_bounded_request_and_extracts_result(self) -> None:
        response = FakeResponse('<div class="t0">Bonjour</div>')
        calls: list[tuple[str, dict[str, object]]] = []

        def fake_get(url: str, **kwargs: object) -> FakeResponse:
            calls.append((url, kwargs))
            return response

        self.assertEqual(translate_text("  hello  ", "fr", request_get=fake_get), "Bonjour")
        self.assertTrue(response.status_checked)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1]["params"], {"sl": "auto", "tl": "fr", "q": "hello"})
        self.assertEqual(calls[0][1]["timeout"], TRANSLATION_TIMEOUT)
        self.assertFalse(calls[0][1]["allow_redirects"])

    def test_translation_timeout_propagates_for_safe_ui_handling(self) -> None:
        def timeout_get(_url: str, **_kwargs: object) -> FakeResponse:
            raise requests.Timeout("private upstream detail")

        with self.assertRaises(requests.Timeout):
            translate_text("hello", "fr", request_get=timeout_get)

    def test_tts_returns_bytes_and_closes_memory_buffer(self) -> None:
        created: list[BytesIO] = []
        calls: list[dict[str, object]] = []

        def buffer_factory() -> BytesIO:
            buffer = BytesIO()
            created.append(buffer)
            return buffer

        class FakeTTS:
            def __init__(self, **kwargs: object) -> None:
                calls.append(kwargs)

            def write_to_fp(self, output: BytesIO) -> None:
                output.write(b"mp3-bytes")

        result = create_audio_bytes(
            "Bonjour",
            "fr",
            tts_factory=FakeTTS,
            buffer_factory=buffer_factory,
        )
        self.assertEqual(result, b"mp3-bytes")
        self.assertEqual(calls[0]["timeout"], TTS_TIMEOUT)
        self.assertTrue(created[0].closed)

    def test_tts_closes_memory_buffer_after_failure(self) -> None:
        created: list[BytesIO] = []

        def buffer_factory() -> BytesIO:
            buffer = BytesIO()
            created.append(buffer)
            return buffer

        class FailingTTS:
            def __init__(self, **_kwargs: object) -> None:
                pass

            def write_to_fp(self, output: BytesIO) -> None:
                output.write(b"partial")
                raise RuntimeError("upstream detail")

        with self.assertRaises(RuntimeError):
            create_audio_bytes(
                "Bonjour",
                "fr",
                tts_factory=FailingTTS,
                buffer_factory=buffer_factory,
            )
        self.assertTrue(created[0].closed)

    def test_tts_uses_verified_tls_and_timeout_for_google_requests(self) -> None:
        encoded_audio = base64.b64encode(b"mp3-bytes").decode("ascii")
        line = f'prefix jQ1olc","[\\"{encoded_audio}\\"]'.encode("utf-8")
        calls: list[dict[str, object]] = []

        class FakeResponse:
            status_code = 200
            reason = "OK"
            closed = False

            def raise_for_status(self) -> None:
                pass

            def iter_lines(self, *, chunk_size: int) -> list[bytes]:
                self.chunk_size = chunk_size
                return [line]

            def close(self) -> None:
                self.closed = True

        response = FakeResponse()

        class FakeSession:
            def send(self, **kwargs: object) -> FakeResponse:
                calls.append(kwargs)
                return response

            def close(self) -> None:
                pass

        with patch("app_logic.requests.Session", side_effect=FakeSession):
            audio = create_audio_bytes("hello", "en")

        self.assertEqual(audio, b"mp3-bytes")
        self.assertTrue(calls[0]["request"].url.startswith("https://"))
        self.assertIs(calls[0]["verify"], True)
        self.assertEqual(calls[0]["timeout"], TTS_TIMEOUT)
        self.assertTrue(response.closed)


if __name__ == "__main__":
    unittest.main()
