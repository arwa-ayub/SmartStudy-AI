from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv
import json
import re

# =============================
# 🔐 LOAD ENV
# =============================
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="SmartStudy AI", layout="wide")

# =============================
# 🧠 SESSION STATE
# =============================
if "conversations" not in st.session_state:
    st.session_state.conversations = {"New Chat": []}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = "New Chat"

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = []

# =============================
# 🧠 HELPERS
# =============================
def detect_confusion(text):
    text = text.lower()
    score = 0
    if "dont understand" in text or "confused" in text:
        score += 2
    if "why" in text:
        score += 1
    if "how" in text:
        score += 2 if len(text.split()) < 5 else 1
    if len(text.split()) < 4:
        score += 1
    return score


def generate_chat_title(text):
    text = re.sub(r"\s+", " ", text.strip())
    prefixes = ["what is", "how", "why", "explain"]
    for p in prefixes:
        if text.lower().startswith(p):
            text = text[len(p):]
    return text[:30].capitalize()


def generate_mcq_quiz(topic, num):
    prompt = f"""
Generate {num} MCQs about {topic}.
Return ONLY JSON.

[
  {{
    "question": "...",
    "options": ["A","B","C","D"],
    "correct_answer": "...",
    "reason": "..."
  }}
]
"""
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    raw = res.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "")
    return json.loads(raw)

# =============================
# 📂 SIDEBAR
# =============================
with st.sidebar:
    st.title("📚 SmartStudy AI")

    mode = st.radio("Mode", ["Chat", "Quiz"])

    if st.button("➕ New Chat"):
        st.session_state.conversations["New Chat"] = []
        st.session_state.current_chat = "New Chat"
        st.rerun()

    st.markdown("### Chats")

    for chat in list(st.session_state.conversations.keys()):
        col1, col2 = st.columns([6,1])

        with col1:
            if st.button(chat, key=f"chat_{chat}", use_container_width=True):
                st.session_state.current_chat = chat
                st.rerun()

        with col2:
            with st.popover("⋮"):
                new_name = st.text_input("Rename", key=f"rename_{chat}")
                if st.button("Rename", key=f"rename_btn_{chat}"):
                    if new_name:
                        st.session_state.conversations[new_name] = st.session_state.conversations.pop(chat)
                        st.session_state.current_chat = new_name
                        st.rerun()

                if st.button("Delete", key=f"delete_{chat}"):
                    del st.session_state.conversations[chat]
                    if not st.session_state.conversations:
                        st.session_state.conversations["New Chat"] = []
                    st.session_state.current_chat = list(st.session_state.conversations.keys())[0]
                    st.rerun()

# =============================
# 💬 CHAT MODE
# =============================
if mode == "Chat":
    messages = st.session_state.conversations[st.session_state.current_chat]

    if not messages:
        st.markdown("<h3 style='text-align:center;color:gray;margin-top:100px;'>Hi 👋, how can I help you?</h3>", unsafe_allow_html=True)

    for msg in messages:
        if msg["role"] == "user":
            st.markdown(f"<div style='text-align:right;'><div style='background:#DCF8C6;padding:10px;border-radius:10px;display:inline-block'>{msg['content']}</div></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align:left;'><div style='background:#F1F0F0;padding:10px;border-radius:10px;display:inline-block'>{msg['content']}</div></div>", unsafe_allow_html=True)

    user_input = st.chat_input("Ask something...")

    if user_input:
        messages.append({"role": "user", "content": user_input})

        if st.session_state.current_chat == "New Chat":
            title = generate_chat_title(user_input)
            st.session_state.conversations[title] = st.session_state.conversations.pop("New Chat")
            st.session_state.current_chat = title
            messages = st.session_state.conversations[title]

        system_prompt = "Explain simply with example" if detect_confusion(user_input) > 2 else "Explain clearly"

        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": system_prompt}] + messages
        )

        reply = res.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        st.rerun()

# =============================
# 🧪 QUIZ MODE
# =============================
else:
    st.title("🧪 Quiz Generator")

    topic = st.text_input("Topic")
    num = st.slider("Number of questions", 3, 20, 5)

    if st.button("Generate Quiz") and topic:
        st.session_state.quiz_data = generate_mcq_quiz(topic, num)

    for i, q in enumerate(st.session_state.quiz_data):
        st.markdown(f"### Q{i+1}: {q['question']}")

        choice = st.radio("Select answer", q["options"], key=f"q{i}")

        if st.button("Check", key=f"check{i}"):
            if choice == q["correct_answer"]:
                st.success("Correct ✅")
            else:
                st.error("Wrong ❌")

            st.info(f"Answer: {q['correct_answer']}")
            st.write("Reason:", q["reason"])