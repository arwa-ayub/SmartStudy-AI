import os
import json
import re
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

# =============================
# 🔐 CONFIG & PREMIUM STYLING
# =============================
load_dotenv()
api_key = os.getenv("GROQ_API_KEY") 
if not api_key:
    st.error("Missing GROQ_API_KEY!")
    st.stop()

client = Groq(api_key=api_key)

st.set_page_config(page_title="SmartStudy AI", layout="wide", page_icon="📚")

st.markdown("""
    <style>
    .stApp { background: white; }
    .centered-greeting { text-align: center; margin-top: 10%; color: #555; font-size: 28px; }
    .user-bubble { background-color: #dcfce7; padding: 12px 18px; border-radius: 20px 20px 5px 20px; margin-bottom: 10px; max-width: 75%; float: right; clear: both; }
    .assistant-bubble { background-color: #f3f4f6; padding: 12px 18px; border-radius: 20px 20px 20px 5px; margin-bottom: 10px; max-width: 75%; float: left; clear: both; }
    .report-card { background-color: #ffffff; border-radius: 15px; padding: 30px; text-align: center; border: 2px solid #f0f2f6; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin: 20px 0; }
    div[data-testid="stSidebar"] { background-color: #f8f9fa; }
    div.stButton > button:first-child { width: auto !important; padding-left: 30px; padding-right: 30px; }
    </style>
""", unsafe_allow_html=True)

# =============================
# 🧠 CORE LOGIC
# =============================
def generate_brief_title(first_question):
    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": f"Provide a 2-3 word title for this topic: {first_question}. Do not use quotes."}],
            max_tokens=10
        )
        return res.choices[0].message.content.strip()
    except:
        return "New Session"

def generate_mcq_quiz(topic, num, difficulty):
    try:
        prompt = f"Generate a JSON array of {num} {difficulty} level MCQs about {topic}. Format: [{{'question': '...', 'options': ['...', '...', '...', '...'], 'correct_answer': '...', 'reason': '...'}}]"
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": "Output ONLY a raw JSON array."}, {"role": "user", "content": prompt}],
            temperature=0.5
        )
        json_match = re.search(r"\[.*\]", res.choices[0].message.content, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else []
    except:
        return []

# =============================
# 📂 STATE MANAGEMENT
# =============================
if "conversations" not in st.session_state: st.session_state.conversations = {"New Chat": []}
if "current_chat" not in st.session_state: st.session_state.current_chat = "New Chat"
if "quiz_data" not in st.session_state: st.session_state.quiz_data = None
if "test_submitted" not in st.session_state: st.session_state.test_submitted = False
if "user_answers" not in st.session_state: st.session_state.user_answers = {}

# =============================
# 📂 SIDEBAR
# =============================
with st.sidebar:
    st.markdown("## 📚 SmartStudy AI")
    st.write("Mode")
    mode = st.radio("Mode", ["Chat", "Quiz"], label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ New Chat"):
        new_name = f"New Chat {len(st.session_state.conversations) + 1}"
        st.session_state.conversations[new_name] = []
        st.session_state.current_chat = new_name
        st.rerun()

    st.write("### Chats")
    for chat in list(st.session_state.conversations.keys()):
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(chat, key=f"btn_{chat}", use_container_width=True):
                st.session_state.current_chat = chat
                st.rerun()
        with col2:
            with st.popover("⋮"):
                if st.button("Delete", key=f"del_{chat}"):
                    del st.session_state.conversations[chat]
                    if not st.session_state.conversations: st.session_state.conversations = {"New Chat": []}
                    st.session_state.current_chat = list(st.session_state.conversations.keys())[0]
                    st.rerun()

# =============================
# 💬 CHAT MODE (GPT STYLE)
# =============================
if mode == "Chat":
    history = st.session_state.conversations[st.session_state.current_chat]
    if not history:
        st.markdown('<div class="centered-greeting">Hi 👋, how can I help you?</div>', unsafe_allow_html=True)
    else:
        for m in history:
            if m["role"] != "system":
                cls = "user-bubble" if m["role"] == "user" else "assistant-bubble"
                st.markdown(f'<div class="{cls}">{m["content"]}</div>', unsafe_allow_html=True)
        st.markdown('<div style="clear:both;"></div>', unsafe_allow_html=True)
    
    if prompt := st.chat_input("Ask something..."):
        # Brief Auto-Naming
        if "New Chat" in st.session_state.current_chat and not history:
            brief_title = generate_brief_title(prompt)
            st.session_state.conversations[brief_title] = st.session_state.conversations.pop(st.session_state.current_chat)
            st.session_state.current_chat = brief_title
            history = st.session_state.conversations[brief_title]
            
            # HIDDEN SYSTEM INSTRUCTION (Behavior like ChatGPT)
            history.append({
                "role": "system", 
                "content": "You are an educational assistant. By default, provide balanced, moderate-length answers. If the user asks for a specific length (one line, short, detailed), follow that instruction strictly. Do not label the answer sections."
            })

        history.append({"role": "user", "content": prompt})
        
        with st.spinner("Thinking..."):
            res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=history)
            history.append({"role": "assistant", "content": res.choices[0].message.content})
        st.rerun()

# ===============================
# 🧪 QUIZ MODE (EXAM STYLE)
# ===============================
else:
    st.markdown("## Quiz")
    
    if not st.session_state.quiz_data:
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            topic = col1.text_input("Enter Topic")
            num = col2.select_slider("Questions", options=list(range(1, 21)), value=5)
            diff = col3.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
            if st.button("Start Test"):
                if not topic.strip():
                    st.warning("⚠️ Please enter a topic first!")
                else:
                    st.session_state.quiz_data = generate_mcq_quiz(topic, num, diff)
                    st.session_state.test_submitted = False
                    st.session_state.user_answers = {}
                    st.rerun()

    if st.session_state.quiz_data:
        for i, q in enumerate(st.session_state.quiz_data):
            with st.container(border=True):
                st.write(f"**Question {i+1}:** {q['question']}")
                choice = st.radio("Options", q['options'], key=f"exam_q_{i}", index=None, disabled=st.session_state.test_submitted)
                st.session_state.user_answers[i] = choice

                if st.session_state.test_submitted:
                    user_choice = st.session_state.user_answers.get(i)
                    if user_choice == q['correct_answer']:
                        st.success("Correct!")
                    else:
                        st.error(f"Incorrect. The right answer is: {q['correct_answer']}")
                    st.info(f"**Reason:** {q['reason']}")

        if not st.session_state.test_submitted:
            st.markdown("---")
            if st.button("Submit Test"):
                st.session_state.test_submitted = True
                st.rerun()
        else:
            correct_count = sum(1 for i, q in enumerate(st.session_state.quiz_data) 
                                if st.session_state.user_answers.get(i) == q['correct_answer'])
            score = (correct_count / len(st.session_state.quiz_data)) * 100
            if score >= 50: st.balloons()
            st.markdown(f'<div class="report-card"><h2>Final Score: {score:.0f}%</h2><p>{correct_count} correct</p></div>', unsafe_allow_html=True)
            if st.button("🔄 Start New Quiz"):
                st.session_state.quiz_data = None
                st.rerun()