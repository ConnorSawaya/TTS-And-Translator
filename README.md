# TTS and Translator

A small Streamlit app that translates text and creates an MP3 using Google Translate and Google Text-to-Speech.

![Translator interface](https://github.com/user-attachments/assets/8dfc79e6-41ad-42d0-bb85-6d7856c40c41)

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run main.py
```

Run the offline safety tests and syntax check with:

```bash
python -m unittest discover -s tests -v
python -m py_compile app_logic.py main.py
```

## Privacy and request limits

- No account, API key, database, or file upload is required.
- Submitted text is sent to Google Translate. The translated text is sent to Google Text-to-Speech. Those are external services and may rate-limit requests or change their free endpoints.
- Text input is limited to 2,000 characters. Translation and speech requests verify TLS and have explicit connection/read timeouts.
- A Streamlit session can make up to three accepted requests per rolling minute, with at least ten seconds between requests.
- Generated MP3 bytes stay in the current Streamlit page/session memory; the app does not write audio files to disk.
- Upstream failures show a generic message so provider details and submitted text are not echoed into the page.

The per-session request limit is a modest guard for normal use. A visitor can reset a session or distribute requests, so it does not replace host-level IP or edge rate limiting on a public deployment.

## Railway deployment

The included `Procfile` starts Streamlit on Railway's `$PORT` and binds to `0.0.0.0`. The app requires no secrets or persistent storage. Keep Streamlit's CORS and XSRF protections enabled, and configure a host-level request limit before exposing the app publicly.
