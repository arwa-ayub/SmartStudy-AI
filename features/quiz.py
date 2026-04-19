import re
import random
import streamlit as st

from core.llm import call_llm
from core.utils import esc, parse_json_array


def _clean_text(value):
    value = str(value or "").strip()
    value = re.sub(r'^[A-Da-d][\.\)\-\:]\s*', '', value)
    return value.strip()


def _looks_like_letter_only(value):
    value = str(value or "").strip().upper()
    return value in {"A", "B", "C", "D"}


def _normalize_quiz_data(raw_data):
    cleaned_quiz = []

    for item in raw_data:
        if not isinstance(item, dict):
            continue

        question = str(item.get("question", "")).strip()
        raw_options = item.get("options", [])
        correct_raw = str(item.get("correct_answer", "")).strip()
        reason = str(item.get("reason", "")).strip() or "No explanation available."

        if not question:
            continue

        if not isinstance(raw_options, list):
            raw_options = []

        cleaned_options = []
        option_map_by_letter = {}

        for idx, opt in enumerate(raw_options):
            cleaned_opt = _clean_text(opt)

            if not cleaned_opt:
                continue

            if len(cleaned_opt) == 1 and cleaned_opt.upper() in {"A", "B", "C", "D"}:
                continue

            letter = chr(65 + idx)
            option_map_by_letter[letter] = cleaned_opt

            if cleaned_opt not in cleaned_options:
                cleaned_options.append(cleaned_opt)

        correct_answer = _clean_text(correct_raw)

        if _looks_like_letter_only(correct_answer):
            mapped = option_map_by_letter.get(correct_answer.upper())
            if mapped:
                correct_answer = mapped

        if not correct_answer and cleaned_options:
            correct_answer = cleaned_options[0]

        if correct_answer and correct_answer not in cleaned_options:
            cleaned_options.append(correct_answer)

        cleaned_options = [opt for opt in cleaned_options if opt]

        deduped = []
        for opt in cleaned_options:
            if opt not in deduped:
                deduped.append(opt)
        cleaned_options = deduped

        if len(cleaned_options) < 2:
            continue

        if len(cleaned_options) > 4:
            if correct_answer in cleaned_options:
                others = [o for o in cleaned_options if o != correct_answer][:3]
                cleaned_options = others + [correct_answer]
            else:
                cleaned_options = cleaned_options[:4]

        random.shuffle(cleaned_options)

        cleaned_quiz.append({
            "question": question,
            "options": cleaned_options,
            "correct_answer": correct_answer,
            "reason": reason,
        })

    return cleaned_quiz


def _generate_quiz(topic, n, diff):
    prompt = f"""
Generate exactly {n} multiple choice questions about "{topic}" at {diff} difficulty.

Return ONLY valid JSON.
Do not write markdown.
Do not write explanations outside JSON.
Do not label answers as A, B, C, D outside the options array.

Use this exact format:
[
  {{
    "question": "Question text",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "correct_answer": "One of the options exactly",
    "reason": "Short explanation"
  }}
]
"""

    raw = call_llm([{"role": "user", "content": prompt}], temperature=0.4)
    parsed = parse_json_array(raw)
    return _normalize_quiz_data(parsed)


def render_quiz_page():
    st.markdown(
        '<div style="text-align:center; margin-top:1.5rem; font-size:40px; font-weight:700;">Smart Quiz</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div style="text-align:center; color:#6b7280; margin-bottom:1.5rem;">Create a topic-based assessment and review your answers clearly.</div>',
        unsafe_allow_html=True
    )

    if not st.session_state.quiz_data:
        c1, c2, c3 = st.columns([2.2, 1, 1])

        with c1:
            topic = st.text_input(
                "Topic",
                value=st.session_state.quiz_topic,
                placeholder="e.g. Neural Networks, Photosynthesis, Laplace Transform"
            )

        with c2:
            n = st.select_slider("Questions", options=list(range(1, 21)), value=st.session_state.quiz_n)

        with c3:
            diff = st.selectbox(
                "Difficulty",
                ["Easy", "Medium", "Hard"],
                index=["Easy", "Medium", "Hard"].index(st.session_state.quiz_diff)
            )

        st.session_state.quiz_topic = topic
        st.session_state.quiz_n = n
        st.session_state.quiz_diff = diff

        if st.button("Generate Quiz", use_container_width=True):
            if not topic.strip():
                st.warning("Please enter a topic.")
            else:
                with st.spinner("Generating quiz..."):
                    quiz_data = _generate_quiz(topic.strip(), n, diff)

                if not quiz_data:
                    st.error("Failed to generate quiz. Try a clearer topic.")
                else:
                    st.session_state.quiz_data = quiz_data
                    st.session_state.user_answers = {}
                    st.session_state.submitted = False
                    st.rerun()

    if st.session_state.quiz_data:
        for i, q in enumerate(st.session_state.quiz_data):
            st.markdown('<div class="quiz-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="q-title">Q{i+1}. {esc(q["question"])}</div>', unsafe_allow_html=True)

            selected = st.radio(
                "Choose one",
                q["options"],
                key=f"opt_{i}",
                index=None,
                disabled=st.session_state.submitted,
                label_visibility="collapsed"
            )

            st.session_state.user_answers[i] = selected

            if st.session_state.submitted:
                correct = q["correct_answer"]
                is_correct = selected == correct

                st.markdown(
                    f"""
                    <div class="feedback">
                      <div><strong>{"Correct" if is_correct else "Incorrect"}</strong></div>
                      <div>Your answer: {esc(selected if selected else "No answer")}</div>
                      <div>Correct answer: {esc(correct)}</div>
                      <div style="margin-top:6px;"><strong>Reason:</strong> {esc(q["reason"])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown('</div>', unsafe_allow_html=True)

        if not st.session_state.submitted:
            if st.button("Submit Test", use_container_width=True):
                st.session_state.submitted = True
                st.rerun()
        else:
            total = len(st.session_state.quiz_data)
            correct_count = sum(
                1 for i, q in enumerate(st.session_state.quiz_data)
                if st.session_state.user_answers.get(i) == q["correct_answer"]
            )

            score = int((correct_count / total) * 100) if total else 0

            verdict = (
                "Excellent work." if score >= 80 else
                "Good effort." if score >= 60 else
                "Keep practicing." if score >= 40 else
                "Needs revision."
            )

            st.markdown(
                f"""
                <div class="report">
                  <div class="score">{score}%</div>
                  <div>{correct_count} out of {total} correct</div>
                  <div style="color:#6b7280; margin-top:6px;">{esc(verdict)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            cA, cB = st.columns(2)

            with cA:
                if st.button("Start New Quiz", use_container_width=True):
                    st.session_state.quiz_data = None
                    st.session_state.user_answers = {}
                    st.session_state.submitted = False
                    st.session_state.quiz_topic = ""
                    st.rerun()

            with cB:
                if st.button("Retry Same Quiz", use_container_width=True):
                    st.session_state.user_answers = {}
                    st.session_state.submitted = False
                    st.rerun()