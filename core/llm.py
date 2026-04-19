import os
import streamlit as st
from groq import Groq

SYSTEM_PROMPT = """
You are SmartStudy Assistant.

Rules:
- Default response language is English.
- Only change language if the user explicitly asks for another language.
- Do not translate unless the user requests it.
- Keep answers clear, accurate, and moderately detailed.
"""


def get_client():
    api_key = os.getenv("GROQ_API_KEY")
    return Groq(api_key=api_key)


def call_llm(messages, temperature=0.4, max_tokens=None):
    try:
        client = get_client()

        kwargs = {
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        res = client.chat.completions.create(**kwargs)
        return res.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"API error: {e}")
        return None