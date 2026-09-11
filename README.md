# TTS-And-Translator
TTS And Translator Website i made for free using google and gTTS
Uses free google translate and free tts
streamlit and railway.com for free hosting!!


simply go to https://tts-and-translator-production.up.railway.app/

Put ur text in,
select your language
click translate
play the audio or download it for whatever you want

<img width="1919" height="965" alt="ttsandtranslator" src="https://github.com/user-attachments/assets/8dfc79e6-41ad-42d0-bb85-6d7856c40f70" />


## Install & Run (one command)
``bash
pip install -r requirements.txt
streamlit run main.py
``n## Test
``bash
python -m py_compile main.py
``n## Env
No API key (see .env.example). Needs internet for Google translate/TTS; offline shows a friendly error instead of a traceback.
## Deploy (Railway)
Procfile present: python -m streamlit run main.py --server.port $PORT --server.address 0.0.0.0.
