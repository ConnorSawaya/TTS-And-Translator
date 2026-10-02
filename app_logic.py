"""Small, testable helpers for bounded translation and speech requests."""

from __future__ import annotations

import base64
from io import BytesIO
from math import ceil
import re
from typing import Callable
import urllib.request

import requests
from bs4 import BeautifulSoup
from gtts import gTTS
from gtts.tts import gTTSError

MAX_INPUT_CHARACTERS = 2_000
REQUEST_COOLDOWN_SECONDS = 10
REQUEST_WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 3
TRANSLATION_TIMEOUT = (3.05, 10)
TTS_TIMEOUT = (3.05, 15)
GOOGLE_TRANSLATE_URL = "https://translate.google.com/m"
USER_SAFE_ERROR_MESSAGE = "Translation is unavailable right now. Please try again shortly."


def validate_input(text: str) -> str:
    """Trim and validate user text before it is sent to an external service."""
    if not isinstance(text, str):
        raise ValueError("Enter text to translate.")

    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Enter text to translate.")
    if len(cleaned) > MAX_INPUT_CHARACTERS:
        raise ValueError(f"Keep the text to {MAX_INPUT_CHARACTERS:,} characters or fewer.")
    return cleaned


def seconds_until_allowed(now: float, request_times: list[float]) -> int:
    """Return the session cooldown in seconds, or zero when a request is allowed."""
    active_times = sorted(
        timestamp
        for timestamp in request_times
        if 0 <= now - timestamp < REQUEST_WINDOW_SECONDS
    )
    if not active_times:
        return 0

    cooldown_remaining = REQUEST_COOLDOWN_SECONDS - (now - active_times[-1])
    window_remaining = 0
    if len(active_times) >= MAX_REQUESTS_PER_WINDOW:
        window_remaining = (
            active_times[-MAX_REQUESTS_PER_WINDOW]
            + REQUEST_WINDOW_SECONDS
            - now
        )

    return max(0, ceil(max(cooldown_remaining, window_remaining)))


def record_request(now: float, request_times: list[float]) -> list[float]:
    """Return a fresh rolling-window list with the accepted attempt recorded."""
    active_times = [
        timestamp
        for timestamp in request_times
        if 0 <= now - timestamp < REQUEST_WINDOW_SECONDS
    ]
    return [*active_times, now]


def translate_text(
    text: str,
    target_language: str,
    *,
    request_get: Callable[..., object] = requests.get,
) -> str:
    """Translate with the same public Google Translate web endpoint and a timeout."""
    cleaned = validate_input(text)
    response = request_get(
        GOOGLE_TRANSLATE_URL,
        params={"sl": "auto", "tl": target_language, "q": cleaned},
        timeout=TRANSLATION_TIMEOUT,
        allow_redirects=False,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    result = soup.find("div", class_="t0") or soup.find(
        "div", class_="result-container"
    )
    if result is None:
        raise RuntimeError("The translation service returned no result.")

    translated = result.get_text(strip=True)
    if not translated:
        raise RuntimeError("The translation service returned no result.")
    return translated


class VerifiedGoogleTTS(gTTS):
    """Use gTTS request preparation with TLS verification and an explicit timeout.

    gTTS 2.5.4's public ``stream`` method sends HTTPS requests with
    ``verify=False``. This adapter preserves its prepared Google requests while
    sending them through requests with certificate verification enabled.
    """

    def stream(self):
        for prepared_request in self._prepare_requests():
            response = None
            session = requests.Session()
            try:
                response = session.send(
                    request=prepared_request,
                    verify=True,
                    proxies=urllib.request.getproxies(),
                    timeout=self.timeout,
                )
                response.raise_for_status()

                audio_parts = []
                for line in response.iter_lines(chunk_size=1024):
                    decoded_line = line.decode("utf-8")
                    if "jQ1olc" not in decoded_line:
                        continue
                    match = re.search(r'jQ1olc","\[\\"(.*)\\"\]', decoded_line)
                    if match is None:
                        raise gTTSError(tts=self, response=response)
                    audio_parts.append(base64.b64decode(match.group(1).encode("ascii")))

                if not audio_parts:
                    raise gTTSError(tts=self, response=response)
            except requests.exceptions.HTTPError as error:
                raise gTTSError(tts=self, response=response) from error
            except requests.exceptions.RequestException as error:
                raise gTTSError(tts=self) from error
            finally:
                if response is not None:
                    response.close()
                session.close()

            yield from audio_parts


def create_audio_bytes(
    text: str,
    target_language: str,
    *,
    tts_factory: Callable[..., object] = VerifiedGoogleTTS,
    buffer_factory: Callable[[], BytesIO] = BytesIO,
) -> bytes:
    """Generate MP3 bytes in memory and always close the temporary buffer."""
    if not text.strip():
        raise ValueError("There is no translated text to speak.")

    buffer = buffer_factory()
    try:
        tts_factory(
            text=text,
            lang=target_language,
            timeout=TTS_TIMEOUT,
        ).write_to_fp(buffer)
        return buffer.getvalue()
    finally:
        buffer.close()
