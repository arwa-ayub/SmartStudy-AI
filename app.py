import os
from dotenv import load_dotenv
import streamlit as st

from core.state import init_state
from ui.styles import load_styles
from ui.sidebar import render_sidebar
from features.chat import render_chat_page
from features.quiz import render_quiz_page

load_dotenv()

st.set_page_config(
    page_title="SmartStudy AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY in environment.")
    st.stop()

init_state()
load_styles()

mode = render_sidebar()

if mode == "chat":
    render_chat_page()
else:
    render_quiz_page()