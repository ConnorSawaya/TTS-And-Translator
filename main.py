import logging
import time

import streamlit as st

from app_logic import (
    MAX_INPUT_CHARACTERS,
    USER_SAFE_ERROR_MESSAGE,
    create_audio_bytes,
    record_request,
    seconds_until_allowed,
    translate_text,
    validate_input,
)

logger = logging.getLogger(__name__)

# Page Config
st.set_page_config( # Page config stuff its the thing you see at the top of the page like info about it
    page_title="TTS For Free!",
    page_icon="🎙️",
    layout="wide"
)

if 'history' not in st.session_state: # Checks history so you have all the data from that thing
    st.session_state.history = []
 
 # Style for the page and stuff!!
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stTextArea textarea { font-size: 1.1rem !important; }
    .history-card{
            padding: 10px;
            border-radius: 5px;
            border-left: 5px solid #ff4b4b;
            background-color: white;
            margin-bottom: 10px;
            }
           <style>
     """, unsafe_allow_html=True)

# SideBar Settings
st.sidebar.title("Voice Settings!!") # Sidebar Voice settings for different languages
languages = { # Different languages for Different translations
    "English US": "en",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Japanese": "ja"
}

target_lan_name = st.sidebar.selectbox("Select Language:", list(languages.keys())) # Target language bane
target_lang_code = languages[target_lan_name] #graps the code from the list above

text_input = st.text_area(
    'Enter Text To Translate:',
    placeholder="Type Something here...",
    max_chars=MAX_INPUT_CHARACTERS,
)
st.caption(
    f"Up to {MAX_INPUT_CHARACTERS:,} characters. Submitted text is sent to "
    "Google Translate and Google Text-to-Speech."
)




if st.button("Translate & Speak"):
    try:
        cleaned_text = validate_input(text_input)
    except ValueError as error:
        st.warning(str(error))
    else:
        request_times = st.session_state.get("request_times", [])
        now = time.monotonic()
        wait_seconds = seconds_until_allowed(now, request_times)
        if wait_seconds:
            st.warning(f"Please wait {wait_seconds} seconds before trying again.")
        else:
            st.session_state.request_times = record_request(now, request_times)
            with st.spinner("Translating and generating audio..."):
                try:
                    translated_text = translate_text(cleaned_text, target_lang_code)
                    audio_bytes = create_audio_bytes(translated_text, target_lang_code)

                    st.subheader("Results")
                    st.success(f"**Translated ({target_lan_name}):**")
                    st.write(translated_text)
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button(
                        label="Download Translation Button(MP3)",
                        data=audio_bytes,
                        file_name="translated_audio.mp3",
                        mime="audio/mp3",
                    )
                except Exception as error:
                    logger.warning(
                        "Translation request failed (%s)", type(error).__name__
                    )
                    st.error(USER_SAFE_ERROR_MESSAGE)

try:
    bottom = st._bottom  # private API on newer streamlit
except AttributeError:
    bottom = st.container
with bottom: # For the Bottom using streamlit.bottom, also added my github for no reason ig 
    st.write("Made With Love By Connor Sawaya | https://github.com/ConnorSawaya?tab=repositories ") # Shows my repos 
    
