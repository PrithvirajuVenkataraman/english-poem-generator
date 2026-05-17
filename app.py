from concurrent.futures import ThreadPoolExecutor
import html
import json
import re
import time

import requests
import streamlit as st

from database import clear_history, create_database, delete_poem, get_poems, save_poem
from prompts import (
    DEFAULT_MODEL,
    EMOTIONS,
    STYLES,
    build_prompt,
)


OLLAMA_URL = "http://localhost:11434/api/generate"
REQUIRED_FIELDS = [
    "title",
    "poem",
]


def apply_styles():
    st.markdown(
        """
        <style>
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"] {
            visibility: hidden;
        }

        .stApp {
            background: #0b0c10;
            color: #f7f3ea;
        }

        .block-container {
            max-width: 1040px;
            padding-top: 1.5rem;
            padding-bottom: 2.5rem;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }

        .topline {
            color: #d7b56d;
            font-size: 0.68rem;
            font-weight: 800;
            letter-spacing: 0.12rem;
            text-transform: uppercase;
            margin-bottom: 0.55rem;
        }

        .hero-title {
            font-size: 2.65rem;
            line-height: 1.05;
            font-weight: 850;
            letter-spacing: 0;
            margin: 0;
            text-align: center;
        }

        .hero-copy {
            color: #b8b3aa;
            max-width: 620px;
            font-size: 0.95rem;
            line-height: 1.6;
            margin: 0.8rem auto 1.2rem auto;
            text-align: center;
        }

        .editor-panel {
            border: 1px solid #2a2d34;
            border-radius: 8px;
            padding: 1.2rem;
            background: #14161c;
            box-shadow: 0 20px 70px rgba(0, 0, 0, 0.25);
            margin-top: 0.8rem;
        }

        .section {
            border: 1px solid #2a2d34;
            border-radius: 8px;
            padding: 1.2rem 1.3rem;
            background: #14161c;
            margin-top: 1rem;
        }

        .section h3,
        .editor-panel h3 {
            margin-top: 0;
            font-size: 0.98rem;
            color: #f7f3ea;
        }

        .draft-note {
            border: 1px solid #3a3120;
            border-radius: 8px;
            padding: 0.9rem 1rem;
            background: #17130c;
            color: #f3d390;
            margin-top: 1rem;
        }

        .poem-box {
            white-space: pre-wrap;
            line-height: 1.8;
            font-size: 0.96rem;
            color: #f8f0df;
        }

        .byline {
            color: #d7b56d;
            font-size: 0.94rem;
            font-weight: 750;
            margin: 0.2rem 0 0.8rem 0;
        }

        .meta-line {
            color: #b8b3aa;
            font-size: 0.92rem;
            margin-bottom: 0.5rem;
        }

        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div {
            background: #1d2028;
            border-color: #30343f;
            border-radius: 8px;
        }

        .stTextArea textarea:focus {
            border-color: #d7b56d;
            box-shadow: 0 0 0 1px #d7b56d;
        }

        .page-action {
            margin: 0 0 1.4rem 0;
        }

        div.stButton > button {
            width: 100%;
            border-radius: 8px;
            min-height: 2.65rem;
            font-weight: 700;
            font-size: 0.92rem;
            transition: transform 120ms ease, background 120ms ease, border-color 120ms ease;
        }

        div.stButton > button[kind="primary"] {
            border: 1px solid #d7b56d;
            background: #d7b56d;
            color: #101010;
            box-shadow: 0 10px 28px rgba(215, 181, 109, 0.18);
        }

        div.stButton > button[kind="primary"]:hover {
            background: #efcb7e;
            color: #101010;
            border-color: #efcb7e;
            transform: translateY(-1px);
        }

        div.stButton > button[kind="secondary"] {
            border: 1px solid #4b5160;
            background: #181b22;
            color: #f7f3ea;
        }

        div.stButton > button[kind="secondary"]:hover {
            border-color: #d7b56d;
            background: #20242d;
            color: #f7f3ea;
            transform: translateY(-1px);
        }

        div.stButton > button:focus-visible {
            outline: 3px solid rgba(215, 181, 109, 0.35);
            outline-offset: 2px;
        }

        @media (max-width: 900px) {
            .block-container {
                padding-top: 1.25rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .hero-title {
                font-size: 2.1rem;
            }

            .hero-copy {
                font-size: 0.92rem;
            }

            [data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
            }
        }

        @media (max-width: 560px) {
            .block-container {
                padding-left: 0.85rem;
                padding-right: 0.85rem;
            }

            .topline {
                font-size: 0.7rem;
                letter-spacing: 0.1rem;
            }

            .hero-title {
                font-size: 1.85rem;
            }

            .hero-copy {
                line-height: 1.55;
            }

            div.stButton > button {
                min-height: 3rem;
                font-size: 0.95rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def parse_poem_json(raw_text):
    """Parse model output, even when it adds a little extra text."""
    try:
        poem_data = json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            raise
        poem_data = json.loads(match.group(0))

    for field in REQUIRED_FIELDS:
        if field not in poem_data:
            poem_data[field] = ""

    return poem_data


def repair_json_with_ollama(raw_text, model_name):
    """Ask Ollama to convert a messy answer into the JSON shape this app needs."""
    repair_prompt = f"""
Convert this text into valid JSON only:

{raw_text}

Use exactly these keys:
title, poem

Rules:
- Return only JSON.
- Do not add markdown.
- Escape poem line breaks with \\n.
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model_name,
            "prompt": repair_prompt,
            "stream": False,
            "format": "json",
        },
        timeout=120,
    )

    response.raise_for_status()
    result = response.json()
    return parse_poem_json(result["response"])


def ask_ollama(prompt, model_name):
    """Send the prompt to Ollama running on this computer."""
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        },
        timeout=120,
    )

    response.raise_for_status()
    result = response.json()
    raw_text = result["response"]

    try:
        return parse_poem_json(raw_text)
    except json.JSONDecodeError:
        return repair_json_with_ollama(raw_text, model_name)


def get_poem_value(poem_data, key, default=""):
    """Read from a generated dict or a SQLite Row."""
    try:
        value = poem_data[key]
    except (KeyError, IndexError):
        value = default

    return value if value not in (None, "") else default


def show_poem(poem_data):
    title = str(poem_data["title"])
    poem = html.escape(str(poem_data["poem"]))
    author_name = str(get_poem_value(poem_data, "author_name", "Anonymous"))
    copy_text = f"{title}\nBy {author_name}\n\n{poem_data['poem']}"

    title_column, copy_column = st.columns([3, 1])
    with title_column:
        st.header(title)
    with copy_column:
        st.download_button(
            "Copy / Save",
            data=copy_text,
            file_name=f"{title[:40] or 'poem'}.txt",
            mime="text/plain",
        )

    st.markdown(
        f'<div class="byline">By {html.escape(author_name)}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="section">
            <h3>Poem</h3>
            <div class="poem-box">{poem}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def generate_with_progress(prompt, model_name):
    """Generate a poem while showing progress until Ollama finishes."""
    loading_area = st.empty()
    steps = [
        "Reading the emotional weather...",
        "Choosing images with sharper edges...",
        "Finding the first honest line...",
        "Shaping the rhythm...",
        "Polishing the final stanza...",
    ]
    progress_value = 0.05
    step_index = 0

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(ask_ollama, prompt, model_name)

        while not future.done():
            current_step = steps[step_index % len(steps)]
            with loading_area.container():
                st.markdown(
                    f'<div class="draft-note">{current_step}</div>',
                    unsafe_allow_html=True,
                )
                st.progress(progress_value)

            progress_value = min(progress_value + 0.03, 0.92)
            step_index += 1
            time.sleep(0.7)

        poem_data = future.result()

    loading_area.empty()
    return poem_data


def generator_page():
    action_left, action_right = st.columns([3, 1])
    with action_right:
        if st.button("View History", type="secondary"):
            st.session_state["page"] = "history"
            st.rerun()

    st.markdown(
        """
        <h1 class="hero-title">Poem Generator</h1>
        <p class="hero-copy">
            Turn a memory, conflict, scene, or feeling into a composed English poem with a clear emotional voice.
        </p>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown("### Compose")
        situation = st.text_area(
            "Situation or Emotional Prompt",
            placeholder="Example: A person waits at a quiet bus stop on a rainy night, remembering a love they never confessed.",
            height=180,
        )
        author_name = st.text_input(
            "Pen Name",
            placeholder="Example: A. River",
        )

        control_left, control_right = st.columns(2)
        with control_left:
            emotion = st.selectbox("Emotion", EMOTIONS)
        with control_right:
            style = st.selectbox("Style", STYLES)

        if st.button("Generate Poem", type="primary"):
            if not situation.strip():
                st.warning("Please enter a situation or emotional prompt.")
                return

            prompt = build_prompt(
                situation,
                emotion,
                style,
                author_name.strip() or "Anonymous",
            )

            try:
                poem_data = generate_with_progress(prompt, DEFAULT_MODEL)
            except requests.exceptions.ConnectionError:
                st.error("Ollama is not running. Start it with: ollama serve")
                return
            except requests.exceptions.HTTPError as error:
                st.error(f"Ollama returned an error: {error}")
                return
            except json.JSONDecodeError:
                st.error("The model did not return valid JSON. Try generating again.")
                return
            except Exception as error:
                st.error(f"Something went wrong: {error}")
                return

            poem_data["situation"] = situation
            poem_data["author_name"] = author_name.strip() or "Anonymous"
            poem_data["output_language"] = "English"
            poem_data["emotion"] = emotion
            poem_data["style"] = style
            poem_data["poetic_influence"] = "none"
            poem_data["english_meaning"] = ""
            poem_data["emotional_theme"] = ""
            poem_data["alternate_ending"] = ""

            save_poem(poem_data)
            st.success("Poem saved to history.")
            show_poem(poem_data)


def history_page():
    action_left, action_right = st.columns([3, 1])
    with action_right:
        if st.button("Back to Generator", type="secondary"):
            st.session_state["page"] = "create"
            st.rerun()

    st.markdown(
        """
        <div class="topline">Saved work</div>
        <h1 class="hero-title">Poem History</h1>
        <p class="hero-copy">Review, revisit, or remove poems from previous sessions.</p>
        """,
        unsafe_allow_html=True,
    )

    poems = get_poems()
    if not poems:
        st.info("No poems saved yet.")
        return

    if st.button("Clear All History", type="secondary"):
        clear_history()
        st.success("History cleared.")
        st.rerun()

    for poem in poems:
        with st.expander(poem["title"]):
            st.markdown(
                f"""
                <div class="meta-line">
                    By {poem['author_name']} | Emotion: {poem['emotion']} | Style: {poem['style']}
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("**Situation**")
            st.write(poem["situation"])
            show_poem(poem)

            if st.button(
                "Delete This Poem",
                key=f"delete_{poem['id']}",
                type="secondary",
            ):
                delete_poem(poem["id"])
                st.success("Poem deleted.")
                st.rerun()


def main():
    st.set_page_config(
        page_title="Poem Generator",
        page_icon="PG",
        layout="wide",
    )

    apply_styles()
    create_database()

    if "page" not in st.session_state:
        st.session_state["page"] = "create"

    if st.session_state["page"] == "create":
        generator_page()
    else:
        history_page()


if __name__ == "__main__":
    main()
