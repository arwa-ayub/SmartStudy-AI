import os
import json
import re
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

# =============================
# 🔐 INITIALIZE
# =============================
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY!")
    st.stop()

client = Groq(api_key=api_key)
st.set_page_config(page_title="SmartStudy AI", layout="wide", page_icon="📚")

# =============================
# 🧠 ENHANCED HELPERS
# =============================
def detect_confusion(text):
    """Returns True if the user seems to be struggling."""
    text = text.lower()
    score = 0
    if any(word in text for word in ["don't understand", "confused", "lost", "hard", "help"]):
        score += 2
    if len(text.split()) < 5 and ("why" in text or "how" in text):
        score += 2
    return score >= 2

def generate_chat_title(text):
    text = re.sub(r"\s+", " ", text.strip())
    prefixes = ["what is", "how", "why", "explain"]
    for p in prefixes:
        if text.lower().startswith(p):
            text = text[len(p):]
    return text[:25].capitalize() + "..." if len(text) > 25 else text.capitalize()

def generate_mcq_quiz(topic, num):
    try:
        prompt = f"Generate {num} multiple choice questions on {topic} in a JSON array. Include question, options, correct_answer, and reason."
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        raw = res.choices[0].message.content
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        return json.loads(match.group(0)) if match else []
    except:
        return []

# =============================
# 📂 SESSION STATE
# =============================
if "conversations" not in st.session_state:
    st.session_state.conversations = {"New Chat": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "New Chat"

# =============================
# 📂 SIDEBAR
# =============================
with st.sidebar:
    st.title("📚 SmartStudy AI")
    mode = st.radio("Mode", ["💬 Chat", "🧪 Quiz"])
    if st.button("➕ New Chat", use_container_width=True):
        new_name = f"Chat {len(st.session_state.conversations) + 1}"
        st.session_state.conversations[new_name] = []
        st.session_state.current_chat = new_name
        st.rerun()
    
    st.divider()
    for chat in list(st.session_state.conversations.keys()):
        col1, col2 = st.columns([5,1])
        with col1:
            if st.button(chat, key=f"b_{chat}", use_container_width=True):
                st.session_state.current_chat = chat
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"d_{chat}"):
                del st.session_state.conversations[chat]
                st.session_state.current_chat = list(st.session_state.conversations.keys())[0] if st.session_state.conversations else "New Chat"
                st.rerun()

# =============================
# 💬 CHAT MODE (With Confusion Logic)
# =============================
if mode == "💬 Chat":
    st.title(f"💬 {st.session_state.current_chat}")
    messages = st.session_state.conversations.get(st.session_state.current_chat, [])

    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask me anything..."):
        # 1. Add User Message
        messages.append({"role": "user", "content": prompt})
        
        # 2. Rename Chat if needed
        if st.session_state.current_chat.startswith("Chat"):
            new_title = generate_chat_title(prompt)
            st.session_state.conversations[new_title] = st.session_state.conversations.pop(st.session_state.current_chat)
            st.session_state.current_chat = new_title

        with st.chat_message("user"):
            st.markdown(prompt)

        # 3. DETECTION: Is the user confused?
        is_confused = detect_confusion(prompt)
        
        # 4. PREPARE PROMPT:
        # If confused, we add a "System Instruction" temporarily
        api_messages = messages.copy()
        if is_confused:
            api_messages.append({
                "role": "system", 
                "content": "The user is confused. Explain the answer using a very simple analogy (like explaining to a 10-year-old) and avoid complex terms."
            })
            st.caption("✨ *SmartStudy is simplifying this for you...*")

        # 5. GENERATE RESPONSE
        with st.chat_message("assistant"):
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=api_messages
            )
            reply = response.choices[0].message.content
            st.markdown(reply)
            messages.append({"role": "assistant", "content": reply})

# ===============================
# 🧪 QUIZ MODE
# ===============================
else:
    st.title("🧪 Quiz Generator")
    topic = st.text_input("Topic")
    if st.button("Generate Quiz") and topic:
        st.session_state.quiz_data = generate_mcq_quiz(topic, 5)
        st.session_state.quiz_checked = {}
        st.rerun()

    if "quiz_data" in st.session_state:
        for i, q in enumerate(st.session_state.quiz_data):
            st.markdown(f"**Q{i+1}: {q['question']}**")
            choice = st.radio("Options", q["options"], key=f"q_{i}", index=None)
            if st.button(f"Check Q{i+1}", key=f"c_{i}"):
                st.session_state.quiz_checked[i] = True
            
            if st.session_state.quiz_checked.get(i):
                if choice == q["correct_answer"]:
                    st.success("Correct!")
                else:
                    st.error(f"Incorrect. Answer: {q['correct_answer']}")
                st.info(f"Reason: {q['reason']}")
            st.divider()