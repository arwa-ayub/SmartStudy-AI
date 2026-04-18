from dotenv import load_dotenv
import os
import streamlit as st
from groq import Groq
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

# ===============================
# 🧠 GENERATE MCQ QUIZ FUNCTION
# ===============================
def generate_mcq_quiz(topic, num):
    try:
        prompt = f"""
        Generate {num} multiple choice questions on the topic: {topic}

        Rules:
        - Each question must have 4 options
        - Only 1 correct answer
        - Include a short reason for the correct answer
        - Return ONLY JSON format like below:

        [
          {{
            "question": "Question here",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Option A",
            "reason": "Explanation here"
          }}
        ]
        """

        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        data = res.choices[0].message.content.strip()

        # clean response
        data = data.replace("```json", "").replace("```", "").strip()

        return json.loads(data)

    except Exception as e:
        st.error(f"Quiz generation failed: {e}")
        return []


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

        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages
        )

        reply = res.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        st.rerun()


# ===============================
# 🧪 QUIZ MODE UI
# ===============================
elif mode == "Quiz":

    st.title("🧪 Quiz Generator")

    topic = st.text_input("Topic")
    num = st.slider("Number of questions", 1, 20, 5)

    # initialize session state
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = []

    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}

    if "quiz_checked" not in st.session_state:
        st.session_state.quiz_checked = {}

    # generate quiz
    if st.button("Generate Quiz") and topic:
        st.session_state.quiz_data = generate_mcq_quiz(topic, num)
        st.session_state.quiz_answers = {}
        st.session_state.quiz_checked = {}

    # display quiz
    for i, q in enumerate(st.session_state.quiz_data):

        st.markdown(f"### Q{i+1}: {q['question']}")

        # user selects option
        choice = st.radio(
            "Select answer",
            q["options"],
            key=f"radio_{i}"
        )

        st.session_state.quiz_answers[i] = choice

        # check button
        if st.button("Check", key=f"check_{i}"):

            st.session_state.quiz_checked[i] = True

        # show result AFTER checking
        if st.session_state.quiz_checked.get(i):

            if st.session_state.quiz_answers[i] == q["correct_answer"]:
                st.success("Correct ✅")
            else:
                st.error("Wrong ❌")

            st.info(f"Answer: {q['correct_answer']}")
            st.write(f"Reason: {q['reason']}")

        st.divider()    