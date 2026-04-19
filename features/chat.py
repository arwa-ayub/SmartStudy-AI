import re
import streamlit as st

from core.llm import call_llm, SYSTEM_PROMPT
from core.utils import esc, detect_lang_instruction, generate_short_title_prompt, sanitize_title


def render_chat_page():
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

        for item in history:
            role = item.get("role")
            if role not in {"user", "assistant"}:
                continue

            css_class = "user" if role == "user" else "assistant"
            content = esc(item.get("content", ""))

            st.markdown(
                f'<div class="row {css_class}"><div class="bubble">{content}</div></div>',
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
            if not history and st.session_state.current_chat.startswith("New Chat"):
                title_prompt = generate_short_title_prompt(prompt)
                title = call_llm([{"role": "user", "content": title_prompt}], temperature=0.2) or "New Chat"
                title = sanitize_title(re.sub(r'["\']', "", title))

                old_name = st.session_state.current_chat

                if title not in st.session_state.conversations:
                    st.session_state.conversations[title] = st.session_state.conversations.pop(old_name)
                    st.session_state.current_chat = title
                else:
                    i = 2
                    candidate = f"{title} {i}"
                    while candidate in st.session_state.conversations:
                        i += 1
                        candidate = f"{title} {i}"
                    st.session_state.conversations[candidate] = st.session_state.conversations.pop(old_name)
                    st.session_state.current_chat = candidate

                history = st.session_state.conversations[st.session_state.current_chat]

            history.append({"role": "user", "content": prompt})
            st.session_state._pending_prompt = prompt
            st.session_state._thinking = True
            st.rerun()

    if st.session_state._thinking and st.session_state._pending_prompt:
        user_prompt = st.session_state._pending_prompt
        lang_instruction = detect_lang_instruction(user_prompt)

        messages = (
            [{"role": "system", "content": SYSTEM_PROMPT}]
            + history[-10:]
            + [{"role": "system", "content": lang_instruction}]
        )

        reply = call_llm(messages, temperature=0.4)
        history.append({"role": "assistant", "content": reply or "Something went wrong. Try again."})

        st.session_state._thinking = False
        st.session_state._pending_prompt = None
        st.rerun()