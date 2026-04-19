import streamlit as st


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
    st.session_state._thinking = False
    st.session_state._pending_prompt = None


def delete_chat(name):
    if name in st.session_state.conversations:
        del st.session_state.conversations[name]

    if not st.session_state.conversations:
        st.session_state.conversations = {"New Chat": []}

    st.session_state.current_chat = list(st.session_state.conversations.keys())[0]


def rename_chat(old, new):
    new = " ".join((new or "").split()).strip()[:40]

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


def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="sidebar-title">📚 SmartStudy AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-sub">Minimal AI study assistant</div>', unsafe_allow_html=True)

        if st.button("＋ New chat", use_container_width=True):
            create_new_chat()
            st.rerun()

        mode_label = st.radio("Choose Mode", ["💬 Chat Assistant", "🧪 Quiz Mode"])
        mode = "chat" if "Chat" in mode_label else "quiz"

        st.markdown('<div class="history-h">Chat history</div>', unsafe_allow_html=True)

        for chat_name in list(st.session_state.conversations.keys()):
            c1, c2 = st.columns([10, 1], gap="small")

            with c1:
                if st.button(chat_name, key=f"open_{chat_name}", use_container_width=True):
                    st.session_state.current_chat = chat_name
                    st.rerun()

            with c2:
                with st.popover(""):
                    st.markdown('<div class="dots">⋯</div>', unsafe_allow_html=True)

                    new_name = st.text_input(
                        "Rename",
                        value=chat_name,
                        key=f"rename_{chat_name}",
                        label_visibility="collapsed",
                    )

                    if st.button("Save", key=f"save_{chat_name}", use_container_width=True):
                        rename_chat(chat_name, new_name)
                        st.rerun()

                    if st.button("Delete", key=f"del_{chat_name}", use_container_width=True):
                        delete_chat(chat_name)
                        st.rerun()

    return mode