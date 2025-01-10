import os
import streamlit as st
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
import google.generativeai as gen_ai

# Ensure consistent language detection
DetectorFactory.seed = 0

# Load environment variables
load_dotenv()

# Configure Streamlit page settings
st.set_page_config(
    page_title="Chatbot!",
    page_icon=":robot:",  # Favicon emoji
    layout="wide",  # Page layout option
)

# Load Google API key from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Verify if the API key is set
if not GOOGLE_API_KEY:
    st.error("Google API Key is missing. Please set it in the .env file.")
    st.stop()

# Configure Google Gemini-Pro AI model
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

# List of supported languages by deep-translator
SUPPORTED_LANGUAGES = GoogleTranslator().get_supported_languages(as_dict=True)


# Function to detect and translate text to English
def detect_and_translate_to_english(text):
    try:
        detected_language = detect(text)  # Detect the language
        if detected_language not in SUPPORTED_LANGUAGES:
            detected_language = 'en'  # Default to English if unsupported

        if detected_language != 'en':
            translated_text = GoogleTranslator(source=detected_language, target='en').translate(text)
        else:
            translated_text = text
    except LangDetectException:
        # Handle cases where language detection fails
        detected_language = 'en'
        translated_text = text
    return translated_text


# Function to translate text back to the original detected language
def translate_to_original_language(text, original_language):
    try:
        if original_language not in SUPPORTED_LANGUAGES:
            original_language = 'en'  # Default to English if unsupported

        translated_text = GoogleTranslator(source='en', target=original_language).translate(text)
    except Exception as e:
        # Fallback if translation fails
        print(f"Translation error: {e}")
        translated_text = text
    return translated_text


# Function to translate roles between Gemini-Pro and Streamlit terminology
def translate_role_for_streamlit(user_role):
    if user_role == "model":
        return "assistant"
    else:
        return user_role


# Initialize chat session in Streamlit if not already present
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

# Display the chatbot's title on the page
st.title("🤖 Chatbot")

# Display the chat history
for message in st.session_state.chat_session.history:
    with st.chat_message(translate_role_for_streamlit(message.role)):
        st.markdown(message.parts[0].text)

# Input field for user's message
user_prompt = st.text_area("Enter your prompt....")  # Allow user to enter text in any Indian regional language

if st.button("Send"):
    if user_prompt:
        # Translate user's prompt to English
        english_prompt = detect_and_translate_to_english(user_prompt)

        # Add translated user's message to chat and display it
        st.chat_message("user").markdown(user_prompt)

        # Send translated user's message to Gemini-Pro and get the response
        gemini_response = st.session_state.chat_session.send_message(english_prompt)

        # Translate Gemini-Pro's response back to the original detected language
        original_language = detect(user_prompt)
        response_in_original_language = translate_to_original_language(gemini_response.text, original_language)

        # Display Gemini-Pro's response in the original detected language
        with st.chat_message("assistant"):
            st.markdown(response_in_original_language)
