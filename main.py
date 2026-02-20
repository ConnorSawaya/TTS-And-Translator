import streamlit as st # Main Streamlit thing for the entire code to run 
from deep_translator import GoogleTranslator # Translate Part Free From google cuz i luv googel
from gtts import gTTS # Free TTS kinda has bad voice but it works 
import io 

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

text_input = st.text_area('Enter Text To Translate:', placeholder="Type Something here...") # text box for input!




if st.button("Translate & Speak"): # Button To run all the code of the translation and tts to happen

    if text_input.strip() =="": # if the box is empty when someone clicks on it just tells the user to input something
        st.warning("Put something in the box 🤦")
    else: # basically if theres text go on...
        with st.spinner("Processing..."): # most of the time you wont see this, spinner if its loadin
            try:
                # First We need to Translate the text from the user
                translated_text = GoogleTranslator(source = "auto", target=target_lang_code).translate(text_input) #Uses Free Google Translate to translate the text give


                # Shows the text
                st.subheader("Results")
                st.success(f"**Translated ({target_lan_name}):**") 
                st.write(translated_text) #


                

                # Second We need to do TTS
                tts = gTTS(text=translated_text, lang=target_lang_code)# TTS STUFF!! also uses the language code from the selection to give it to google 

                # Second We need to save the audio to a buffer byte instead of a file cuz streamlits sucks kinda but its easy to use so yeeeahhH!!!
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                audio_fp.seek(0)
                
                # Third-Part 1 We need to display the audio for the user to be able to hear
                st.audio(audio_fp, format="audio/mp3") # Displays the audi for the user as a mp3

                st.download_button(
                    label="Download Translation Button(MP3)"
                    data=audio_fp
                    file_name="translated_audio.mp3",
                    mime="audio/mp3"
                )



        
            except Exception as e:
                st.error(f"An Error Happened: {e}") #Shows if a error happens and it shows it to the user

with st._bottom: # For the Bottom using streamlit.bottomm, also added my github for no reason ig 
    st.write("Made With Love By Connor Sawaya | https://github.com/ConnorSawaya?tab=repositories ") # Shows my repos 
    
