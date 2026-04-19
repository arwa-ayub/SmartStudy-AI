import streamlit as st


def init_state():
    if "conversations" not in st.session_state:
        st.session_state.conversations = {"New Chat": []}

    if "current_chat" not in st.session_state:
        st.session_state.current_chat = list(st.session_state.conversations.keys())[0]

    if "_thinking" not in st.session_state:
        st.session_state._thinking = False

    if "_pending_prompt" not in st.session_state:
        st.session_state._pending_prompt = None

    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = None

    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}

    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if "quiz_topic" not in st.session_state:
        st.session_state.quiz_topic = ""

    if "quiz_n" not in st.session_state:
        st.session_state.quiz_n = 5

    if "quiz_diff" not in st.session_state:
        st.session_state.quiz_diff = "Medium"