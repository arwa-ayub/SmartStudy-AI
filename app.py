import os
import re
from dotenv import load_dotenv
import json
import random
import html
import streamlit as st
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

# =============================
# ⚙️ CONFIG
# =============================
st.set_page_config(page_title="SmartStudy AI", page_icon="📚", layout="wide")

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY in environment.")
    st.stop()

client = Groq(api_key=api_key)

# =============================
# 🧠 SESSION STATE
# =============================
def ensure_state():
    if "conversations" not in st.session_state:
        st.session_state.conversations = {"New Chat": []}
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = list(st.session_state.conversations.keys())[0]
    if "_thinking" not in st.session_state:
        st.session_state._thinking = False
    if "_pending_prompt" not in st.session_state:
        st.session_state._pending_prompt = None

    # Quiz
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

ensure_state()

# =============================
# 🎨 STYLES
# =============================
st.markdown("""
<style>
:root{
  --bg:#ffffff; --panel:#f7f7f8; --border:#e5e7eb; --muted:#6b7280;
}
.stApp{background:var(--bg);}
section[data-testid="stSidebar"]{
  width:260px !important; min-width:260px !important; max-width:260px !important;
  background:var(--panel); border-right:1px solid var(--border);
}
.sidebar-title{font-weight:700; font-size:18px; margin-bottom:6px;}
.sidebar-sub{color:var(--muted); font-size:13px; margin-bottom:12px;}
.history-h{font-size:12px; color:var(--muted); margin:12px 0 6px 2px; font-weight:700; text-transform:uppercase;}
.chat-shell{max-width:900px; margin:0 auto;}
.row{display:flex; margin-bottom:12px;}
.row.user{justify-content:flex-end;}
.row.assistant{justify-content:flex-start;}
.bubble{
  max-width:75%; border:1px solid var(--border); border-radius:16px;
  padding:12px 14px; line-height:1.6; background:#fff; white-space:pre-wrap;
}
.thinking{color:var(--muted); font-style:italic;}
.empty{text-align:center; margin-top:20vh;}
.empty h1{font-size:42px; margin-bottom:8px;}
.empty p{color:var(--muted);}
.quiz-card{
  border:1px solid var(--border); border-radius:16px; padding:16px; margin-bottom:14px; background:#fff;
}
.q-title{font-weight:600; margin-bottom:10px;}
.feedback{
  margin-top:10px; border:1px solid var(--border); border-radius:12px; padding:10px; background:#fafafa;
}
.report{
  border:1px solid var(--border); border-radius:18px; padding:20px; text-align:center; margin:16px 0;
}
.report .score{font-size:34px; font-weight:800;}
            
/* remove button look */
button[kind="secondary"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    min-height: auto !important;
}

/* dots styling */
.dots {
    font-size: 18px;
    color: #9ca3af;
    cursor: pointer;
    text-align: center;
}

/* subtle hover effect */
.dots:hover {
    color: #111827;
}

</style>
""", unsafe_allow_html=True)

# =============================
# 🛠 HELPERS
# =============================
def esc(t: str) -> str:
    return html.escape(str(t)).replace("\n", "<br>")

def create_new_chat():
    base = "New Chat"
    existing = st.session_state.conversations
    if base not in existing:
        name = base
    else:
        i = 2
        while f"{base} {i}" in existing:
            i += 1
        name = f"{base} {i}"
    st.session_state.conversations[name] = []
    st.session_state.current_chat = name

def delete_chat(name):
    if name in st.session_state.conversations:
        del st.session_state.conversations[name]
    if not st.session_state.conversations:
        st.session_state.conversations = {"New Chat": []}
    st.session_state.current_chat = list(st.session_state.conversations.keys())[0]

def rename_chat(old, new):
    new = re.sub(r"\s+", " ", (new or "")).strip()[:40]
    if not new or old not in st.session_state.conversations:
        return
    if new == old:
        return
    final = new
    i = 2
    while final in st.session_state.conversations:
        final = f"{new} {i}"
        i += 1
    st.session_state.conversations[final] = st.session_state.conversations.pop(old)
    if st.session_state.current_chat == old:
        st.session_state.current_chat = final

def detect_lang_instruction(text: str) -> str:
    t = text.lower()
    m = re.search(r"(answer|reply|respond|write|explain)\s+in\s+([a-zA-Z\s]+)", t)
    if m:
        lang = m.group(2).strip(" .,!?:;")
        return f"Answer in {lang}."
    return "Answer in English."

def call_llm(messages, temperature=0.4):
    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=temperature
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"API error: {e}")
        return None

def parse_json_array(text: str):
    if not text:
        return []
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except:
        pass
    m = re.search(r"\[\s*{.*}\s*\]", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            if isinstance(data, list):
                return data
        except:
            pass
    return []

def normalize_quiz(data):
    out = []
    for it in data:
        if not isinstance(it, dict): continue
        q = str(it.get("question","")).strip()
        opts = it.get("options", [])
        ans = str(it.get("correct_answer","")).strip()
        why = str(it.get("reason","")).strip() or "No explanation."
        if not q or not isinstance(opts, list) or len(opts) < 2: continue
        opts = [str(o).strip() for o in opts if str(o).strip()]
        if ans and ans not in opts: opts.append(ans)
        if len(opts) > 4:
            opts = opts[:4]
            if ans not in opts: opts[-1] = ans
        random.shuffle(opts)
        out.append({"question": q, "options": opts, "correct_answer": ans or opts[0], "reason": why})
    return out

def gen_quiz(topic, n, diff):
    prompt = f"""
Generate exactly {n} MCQs about "{topic}" at {diff} difficulty.
Return ONLY JSON (no markdown, no extra text):
[
  {{
    "question": "...",
    "options": ["A","B","C","D"],
    "correct_answer": "one of options",
    "reason": "short explanation"
  }}
]
"""
    txt = call_llm([{"role":"user","content":prompt}], temperature=0.5)
    arr = parse_json_array(txt)
    return normalize_quiz(arr)

# =============================
# 📚 SIDEBAR
# =============================
with st.sidebar:
    st.markdown('<div class="sidebar-title">📚 SmartStudy AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Minimal AI study assistant</div>', unsafe_allow_html=True)

    if st.button("＋ New chat", use_container_width=True):
        create_new_chat()
        st.rerun()

    # ✅ No typing (radio)
    mode = st.radio("Choose Mode", [" Chat Assistant", " Quiz Mode"])

    st.markdown('<div class="history-h">Chat history</div>', unsafe_allow_html=True)

    for chat_name in list(st.session_state.conversations.keys()):
        c1, c2 = st.columns([10, 1], gap="small")

        with c1:
            if st.button(chat_name, key=f"open_{chat_name}", use_container_width=True):
                st.session_state.current_chat = chat_name
                st.rerun()

        with c2:
            # Clean minimal popover (best possible in Streamlit)
            with st.popover(""):
                st.markdown('<div class="dots">⋯</div>', unsafe_allow_html=True)
                new_name = st.text_input(
                    "Rename",
                    value=chat_name,
                    key=f"rename_{chat_name}",
                    label_visibility="collapsed"
                )
                if st.button("Save", key=f"save_{chat_name}", use_container_width=True):
                    rename_chat(chat_name, new_name)
                    st.rerun()
                if st.button("Delete", key=f"del_{chat_name}", use_container_width=True):
                    delete_chat(chat_name)
                    st.rerun()

mode_key = "Chat" if "Chat" in mode else "Quiz"

# =============================
#  CHAT MODE
# =============================
if mode_key == "Chat":
    history = st.session_state.conversations[st.session_state.current_chat]

    if not history and not st.session_state._thinking:
        st.markdown("""
        <div class="empty">
          <h1>Hi! How can I help you?</h1>
          <p>Ask anything and start learning.</p>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown('<div class="chat-shell">', unsafe_allow_html=True)

        for m in history:
            role = m.get("role")
            if role not in {"user","assistant"}: continue
            cls = "user" if role=="user" else "assistant"
            st.markdown(
                f'<div class="row {cls}"><div class="bubble">{esc(m.get("content",""))}</div></div>',
                unsafe_allow_html=True
            )

        if st.session_state._thinking:
            st.markdown(
                '<div class="row assistant"><div class="bubble thinking">Thinking...</div></div>',
                unsafe_allow_html=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

    prompt = st.chat_input("Ask anything...")

    if prompt:
        prompt = prompt.strip()
        if prompt:
            # auto title on first message
            if not history and st.session_state.current_chat.startswith("New Chat"):
                # quick short title via LLM (optional)
                title_prompt = f"Create a 2-4 word title for: {prompt}"
                title = call_llm([{"role":"user","content":title_prompt}], temperature=0.2) or "New Chat"
                title = re.sub(r'["\']','', title).strip()[:40] or "New Chat"
                old = st.session_state.current_chat
                if title not in st.session_state.conversations:
                    st.session_state.conversations[title] = st.session_state.conversations.pop(old)
                    st.session_state.current_chat = title
                else:
                    i=2; cand=f"{title} {i}"
                    while cand in st.session_state.conversations:
                        i+=1; cand=f"{title} {i}"
                    st.session_state.conversations[cand] = st.session_state.conversations.pop(old)
                    st.session_state.current_chat = cand
                history = st.session_state.conversations[st.session_state.current_chat]

            history.append({"role":"user","content":prompt})
            st.session_state._pending_prompt = prompt
            st.session_state._thinking = True
            st.rerun()

    if st.session_state._thinking and st.session_state._pending_prompt:
        user_prompt = st.session_state._pending_prompt
        lang_inst = detect_lang_instruction(user_prompt)
        messages = (
            [{"role":"system","content":"You are a helpful assistant."}]
            + history[-10:]
            + [{"role":"system","content":lang_inst}]
        )
        reply = call_llm(messages, temperature=0.4)
        history.append({"role":"assistant","content": reply or "Something went wrong. Try again."})
        st.session_state._thinking = False
        st.session_state._pending_prompt = None
        st.rerun()

# =============================
#  QUIZ MODE (FINAL FIXED)
# =============================
else:

    def extract_real_text(opt):
        opt = str(opt).strip()

        # Remove labels like A., B), C -
        opt = re.sub(r'^[A-Da-d][\.\)\-\:]\s*', '', opt)

        return opt.strip()

    def normalize_quiz_data(raw_data):
        cleaned = []

        for item in raw_data:
            if not isinstance(item, dict):
                continue

            question = item.get("question", "").strip()
            options = item.get("options", [])
            correct = str(item.get("correct_answer", "")).strip()
            reason = item.get("reason", "No explanation")

            if not question or not options:
                continue

            # Clean options
            options = [extract_real_text(o) for o in options if str(o).strip()]

            # Remove duplicates
            options = list(dict.fromkeys(options))

            # If correct is "A/B/C" → map it
            if len(correct) == 1 and correct.upper() in ["A", "B", "C", "D"]:
                idx = ord(correct.upper()) - ord("A")
                if idx < len(options):
                    correct = options[idx]

            # Ensure correct is valid
            if correct not in options:
                options.append(correct)

            # Limit to 4
            options = options[:4]

            random.shuffle(options)

            cleaned.append({
                "question": question,
                "options": options,
                "correct_answer": correct,
                "reason": reason
            })

        return cleaned


    # UI HEADER
    st.markdown('<div style="text-align:center; font-size:40px; font-weight:700;">Smart Quiz</div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center; color:#6b7280;">Create a topic-based assessment</div>', unsafe_allow_html=True)

    # INPUT
    if not st.session_state.quiz_data:
        c1, c2, c3 = st.columns([2.2, 1, 1])

        with c1:
            topic = st.text_input("Topic", placeholder="e.g. Neural Networks")

        with c2:
            n = st.slider("Questions", 1, 10, 5)

        with c3:
            diff = st.selectbox("Difficulty", ["Easy","Medium","Hard"])

        if st.button("Generate Quiz", use_container_width=True):
            if not topic.strip():
                st.warning("Enter topic")
            else:
                with st.spinner("Generating..."):

                    prompt = f"""
Generate {n} MCQs about {topic} ({diff} level).

Return ONLY JSON:

[
  {{
    "question": "...",
    "options": ["...", "...", "...", "..."],
    "correct_answer": "...",
    "reason": "..."
  }}
]
"""

                    res = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt}]
                    )

                    raw = res.choices[0].message.content

                    try:
                        data = json.loads(raw)
                    except:
                        st.error("Bad AI response")
                        data = []

                    st.session_state.quiz_data = normalize_quiz_data(data)
                    st.session_state.user_answers = {}
                    st.session_state.submitted = False
                    st.rerun()

    # DISPLAY QUIZ
    if st.session_state.quiz_data:

        for i, q in enumerate(st.session_state.quiz_data):

            st.markdown('<div class="quiz-card">', unsafe_allow_html=True)
            st.markdown(f"**Q{i+1}. {q['question']}**")

            selected = st.radio(
                "",
                q["options"],
                key=f"q_{i}",
                index=None,
                disabled=st.session_state.submitted
            )

            st.session_state.user_answers[i] = selected

            if st.session_state.submitted:
                correct = q["correct_answer"]
                is_correct = selected == correct

                st.markdown(f"""
                <div class="feedback">
                    <b>{'Correct' if is_correct else 'Incorrect'}</b><br>
                    Your answer: {selected or 'None'}<br>
                    Correct answer: {correct}<br>
                    <b>Reason:</b> {q['reason']}
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        # SUBMIT
        if not st.session_state.submitted:
            if st.button("Submit"):
                st.session_state.submitted = True
                st.rerun()

        else:
            total = len(st.session_state.quiz_data)
            correct = sum(
                1 for i, q in enumerate(st.session_state.quiz_data)
                if st.session_state.user_answers.get(i) == q["correct_answer"]
            )

            score = int((correct / total) * 100)

            st.markdown(f"""
            <div class="report">
                <div class="score">{score}%</div>
                <div>{correct}/{total} correct</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("New Quiz"):
                st.session_state.quiz_data = None
                st.session_state.user_answers = {}
                st.session_state.submitted = False
                st.rerun()