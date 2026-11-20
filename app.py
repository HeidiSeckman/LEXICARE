import asyncio
import io
import time
import wave
import edge_tts
from google import genai
from google.genai import types
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from lexi_identity import get_lexicare_identity
from safety_shield import (
    check_safety_level,
    render_crisis_card,
    render_distress_grounding,
    render_safety_header,
)

st.set_page_config(
    page_title="LexiCare | Powered by LexiTech",
    page_icon="🌺",
    layout="centered",
)

if "accepted_terms" not in st.session_state:
    st.session_state.accepted_terms = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = True
if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "Just Listen (Vent)"

st.markdown(
    """
    <style>
    @import url('https://googleapis.com');

    /* Rich, Deep Cancun/Hawaii Twilight Lagoon Base (Zero Washed-Out Fade) */
    .stApp {
        background: linear-gradient(160deg, #041318 0%, #092b34 45%, #0d3b44 80%, #05181e 100%) !important;
        color: #ffffff !important;
    }

    /* Keep ALL Content Cards & Chat Boxes Strictly ON TOP of Waterfall & Flowers */
    [data-testid="stAppViewContainer"] > .main,
    [data-testid="stMainBlockContainer"],
    .block-container {
        background: transparent !important;
        position: relative !important;
        z-index: 10 !important;
    }

    p, label, li, .stMarkdown, input, textarea {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #f4f8f6 !important;
    }

    h1, h2, h3 {
        font-family: 'Cormorant Garamond', Georgia, serif !important;
        color: #ffffff !important;
    }

    [data-testid="stHeader"] {
        background: rgba(4, 19, 24, 0.55) !important;
        backdrop-filter: blur(12px);
        z-index: 20 !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #051b22 0%, #082730 100%) !important;
        border-right: 1px solid rgba(235, 213, 179, 0.28);
        z-index: 25 !important;
    }

    /* Hero Sanctuary Card */
    .lexi-hero {
        background: linear-gradient(145deg, rgba(11, 45, 54, 0.92), rgba(5, 23, 29, 0.96));
        border: 1px solid rgba(235, 213, 179, 0.42);
        border-radius: 24px;
        padding: 1.6rem 1.8rem;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 18px 42px rgba(0, 0, 0, 0.48);
    }

    .lexi-hero h1 {
        margin: 0;
        font-size: 2.8rem !important;
        background: linear-gradient(90deg, #ffffff, #f2dec0, #9ef0e0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .lexi-badge {
        display: inline-block;
        margin-top: 0.45rem;
        padding: 0.28rem 1rem;
        border-radius: 999px;
        background: rgba(235, 213, 179, 0.16);
        border: 1px solid rgba(235, 213, 179, 0.45);
        color: #f7e6c8 !important;
        font-size: 0.76rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    /* Rich Frosted Chat Bubbles */
    [data-testid="stChatMessage"] {
        background: rgba(8, 34, 42, 0.92) !important;
        border: 1px solid rgba(132, 212, 198, 0.34);
        border-radius: 18px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.36);
    }

    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stExpander"] {
        background: rgba(7, 29, 36, 0.92) !important;
        border: 1px solid rgba(235, 213, 179, 0.32) !important;
        border-radius: 16px !important;
    }

    .stButton > button {
        border-radius: 12px !important;
        border: 1px solid rgba(235, 213, 179, 0.42) !important;
        background: rgba(12, 48, 58, 0.94) !important;
        color: #ffffff !important;
        transition: all 0.22s ease;
    }

    .stButton > button:hover {
        background: rgba(34, 118, 120, 0.98) !important;
        border-color: #f7e6c8 !important;
        color: #ffffff !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #289488, #196664) !important;
        border: 1px solid #f7e6c8 !important;
    }

    textarea, input, [data-testid="stChatInput"] textarea {
        background-color: rgba(5, 20, 26, 0.96) !important;
        color: #ffffff !important;
        border: 1px solid rgba(235, 213, 179, 0.42) !important;
        border-radius: 14px !important;
    }

    /* Background Sanctuary Layer (Strictly BEHIND All Boxes) */
    .sanctuary-water {
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0 !important;
        overflow: hidden;
    }

    .lotus-flower {
        position: absolute;
        opacity: 0.32;
        filter: drop-shadow(0 0 14px rgba(235, 213, 179, 0.35));
        animation: lotusDrift 18s ease-in-out infinite alternate;
    }

    .lotus-1 { top: 8%; left: 3%; width: 175px; animation-duration: 16s; }
    .lotus-2 { top: 46%; left: 2%; width: 225px; opacity: 0.26; animation-duration: 21s; }
    .lotus-3 { bottom: 10%; left: 7%; width: 155px; animation-duration: 19s; }
    .lotus-4 { top: 16%; right: 14%; width: 165px; opacity: 0.25; animation-duration: 23s; }

    .waterfall-column {
        position: absolute;
        top: 0;
        right: 0;
        width: 145px;
        height: 100vh;
        background: linear-gradient(
            180deg,
            rgba(180, 245, 238, 0.05) 0%,
            rgba(130, 232, 224, 0.24) 45%,
            rgba(195, 250, 244, 0.42) 100%
        );
        mask-image: linear-gradient(90deg, transparent 0%, black 35%, black 100%);
        -webkit-mask-image: linear-gradient(90deg, transparent 0%, black 35%, black 100%);
    }

    .waterfall-streams {
        position: absolute;
        inset: -100% 0 0 0;
        background-image:
            repeating-linear-gradient(
                90deg,
                transparent 0px,
                rgba(220, 252, 248, 0.32) 3px,
                transparent 7px,
                rgba(115, 218, 210, 0.24) 14px,
                transparent 22px
            ),
            radial-gradient(circle at 50% 30%, rgba(255, 255, 255, 0.32) 0%, transparent 60%);
        background-size: 100% 220px, 100% 340px;
        animation: cascadeFall 2.6s linear infinite;
    }

    .waterfall-mist-pool {
        position: absolute;
        bottom: -25px;
        right: -10px;
        width: 280px;
        height: 120px;
        border-radius: 50%;
        background: radial-gradient(
            ellipse at center,
            rgba(215, 252, 248, 0.48) 0%,
            rgba(82, 204, 196, 0.26) 48%,
            transparent 75%
        );
        filter: blur(10px);
        animation: mistPulse 3.8s ease-in-out infinite;
    }

    .lagoon-wave {
        position: absolute;
        bottom: -8px;
        left: 0;
        width: 200%;
        height: 145px;
        animation: waveRoll 14s linear infinite;
    }

    @keyframes lotusDrift {
        0% { transform: translateY(0px) rotate(0deg) scale(1); }
        100% { transform: translateY(-22px) rotate(12deg) scale(1.06); }
    }

    @keyframes cascadeFall {
        0% { transform: translateY(0%); }
        100% { transform: translateY(50%); }
    }

    @keyframes mistPulse {
        0%, 100% { transform: scale(1) translateY(0px); opacity: 0.78; }
        50% { transform: scale(1.14) translateY(-8px); opacity: 1; }
    }

    @keyframes waveRoll {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }
    </style>
    """
)

 <div class="sanctuary-water">
        <svg class="lotus-flower lotus-1" viewBox="0 0 200 200" fill="none" stroke="#ebd5b3" stroke-width="1.8">
            <path d="M100 25 C122 62 122 92 100 115 C78 92 78 62 100 25 Z"/>
            <path d="M100 115 C68 95 45 68 38 40 C68 48 88 75 100 115 Z"/>
            <path d="M100 115 C132 95 155 68 162 40 C132 48 112 75 100 115 Z"/>
            <path d="M100 115 C58 112 28 96 16 74 C46 72 76 88 100 115 Z"/>
            <path d="M100 115 C142 112 172 96 184 74 C154 72 124 88 100 115 Z"/>
            <path d="M45 128 Q100 148 155 128" stroke="#9ef0e0" stroke-width="1.5"/>
        </svg>
        <svg class="lotus-flower lotus-2" viewBox="0 0 200 200" fill="none" stroke="#9ef0e0" stroke-width="1.6">
            <path d="M100 25 C122 62 122 92 100 115 C78 92 78 62 100 25 Z"/>
            <path d="M100 115 C68 95 45 68 38 40 C68 48 88 75 100 115 Z"/>
            <path d="M100 115 C132 95 155 68 162 40 C132 48 112 75 100 115 Z"/>
            <path d="M100 115 C58 112 28 96 16 74 C46 72 76 88 100 115 Z"/>
            <path d="M100 115 C142 112 172 96 184 74 C154 72 124 88 100 115 Z"/>
            <path d="M45 128 Q100 148 155 128" stroke="#ebd5b3" stroke-width="1.5"/>
        </svg>
        <svg class="lotus-flower lotus-3" viewBox="0 0 200 200" fill="none" stroke="#ebd5b3" stroke-width="1.6">
            <path d="M100 25 C122 62 122 92 100 115 C78 92 78 62 100 25 Z"/>
            <path d="M100 115 C68 95 45 68 38 40 C68 48 88 75 100 115 Z"/>
            <path d="M100 115 C132 95 155 68 162 40 C132 48 112 75 100 115 Z"/>
            <path d="M45 128 Q100 148 155 128" stroke="#9ef0e0" stroke-width="1.5"/>
        </svg>
        <svg class="lotus-flower lotus-4" viewBox="0 0 200 200" fill="none" stroke="#ebd5b3" stroke-width="1.6">
            <path d="M100 25 C122 62 122 92 100 115 C78 92 78 62 100 25 Z"/>
            <path d="M100 115 C68 95 45 68 38 40 C68 48 88 75 100 115 Z"/>
            <path d="M100 115 C132 95 155 68 162 40 C132 48 112 75 100 115 Z"/>
            <path d="M45 128 Q100 148 155 128" stroke="#9ef0e0" stroke-width="1.5"/>
async def _generate_free_voice(text: str, output_path: str, rate: str, pitch: str):
    communicate = edge_tts.Communicate(
        text,
        "en-US-AvaMultilingualNeural",
        rate=rate,
        pitch=pitch,
    )
    await communicate.save(output_path)


def speak_text(text: str, mode: str, safety_level: str):
    audio_file = "lexicare_reply.mp3"

    if safety_level == "DISTRESS":
        rate, pitch = "-10%", "-2Hz"
    elif mode == "Just Listen (Vent)":
        rate, pitch = "-6%", "-1Hz"
    elif mode == "Distract Me / Play a Game":
        rate, pitch = "+2%", "+1Hz"
    else:
        rate, pitch = "-3%", "+0Hz"

    try:
        asyncio.run(_generate_free_voice(text, audio_file, rate, pitch))
        st.audio(audio_file, format="audio/mp3", autoplay=True)
    except Exception:
        pass


def generate_lexi_reply(system_instruction: str, messages: list) -> str:
    convo = [m for m in messages if not m.get("is_greeting")][-10:]

    anti_repeat_rule = (
        "\nCRITICAL CONVERSATION RULE: Read the entire conversation history carefully. "
        "NEVER repeat your greeting or repeat sentences you already said. "
        "Always respond directly, warmly, and naturally to the user's latest message."
    )
    full_instruction = system_instruction + anti_repeat_rule
    last_error = ""

    gemini_key = st.secrets.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        client = genai.Client(api_key=gemini_key)
        gemini_contents = []
        for m in convo:
            role = "user" if m["role"] == "user" else "model"
            gemini_contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=m["content"])],
                )
            )
        for model_name in ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=gemini_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=full_instruction,
                        temperature=0.82,
                    ),
                )
                if response.text:
                    return response.text.strip()
            except Exception as e:
                last_error = f"Gemini: {e}"

    groq_key = st.secrets.get("GROQ_API_KEY", "").strip()
    if groq_key:
        try:
            from groq import Groq

            groq_client = Groq(api_key=groq_key)
            available = [
                m.id
                for m in groq_client.models.list().data
                if "whisper" not in m.id.lower()
                and "guard" not in m.id.lower()
                and "tts" not in m.id.lower()
            ]
            preferred = [m for m in available if "llama" in m.lower()] + available

            groq_messages = [{"role": "system", "content": full_instruction}]
            for m in convo:
                groq_messages.append({"role": m["role"], "content": m["content"]})

            for model_id in preferred[:4]:
                try:
                    completion = groq_client.chat.completions.create(
                        model=model_id,
                        messages=groq_messages,
                        temperature=0.82,
                        frequency_penalty=0.6,
                    )
                    reply_text = completion.choices.message.content
                    if reply_text:
                        return reply_text.strip()
                except Exception as e:
                    last_error = f"Groq ({model_id}): {e}"
        except Exception as e:
            last_error = f"Groq init: {e}"

    return f"Connection hiccup ({last_error or 'Missing API key in Streamlit Secrets'}). Check your Secrets tab and try again!"


with st.sidebar:
    st.header("🌊 Spa Soundscapes")
    ambient_choice = st.selectbox(
        "Ambient Sanctuary Audio",
        ["Off", "Ocean Waves", "Soft Rain", "Forest Waterfall"],
    )
    if ambient_choice != "Off":
        sound_bytes = generate_nature_sound(ambient_choice)
        st.audio(sound_bytes, format="audio/wav", loop=True, autoplay=True)
        st.caption(f"Streaming {ambient_choice.lower()} in the background.")

    st.divider()
    st.header("🌺 Sanctuary Mode")
    st.session_state.chat_mode = st.radio(
        "How should Lexi support you?",
        [
            "Just Listen (Vent)",
            "Help Me Problem-Solve",
            "Distract Me / Play a Game",
        ],
    )
    st.session_state.voice_enabled = st.toggle(
        "Lexi Voice Replies (Ava • Unlimited)", value=True
    )

    st.divider()
    st.subheader("🌬️ 60-Second Calm Reset")
    if st.button("Start Guided Breathing", use_container_width=True):
        placeholder = st.empty()
        steps = [
            ("Breathe IN slowly through your nose...", 4),
            ("HOLD gently...", 4),
            ("Breathe OUT slowly through your mouth...", 6),
        ]
        for _ in range(3):
            for label, secs in steps:
                for s in range(secs, 0, -1):
                    placeholder.info(f"**{label}** ({s}s)")
                    time.sleep(1)
        placeholder.success("Nice job. Let your shoulders drop.")

    st.divider()
    st.subheader("🍃 Worry Release")
    worry = st.text_area(
        "Write a thought you want to let go of:",
        placeholder="Type it here, then release it into the tide...",
        height=80,
    )
    if st.button("Release Thought", use_container_width=True):
        if worry.strip():
            st.toast("Released and washed away. 🌊")
            st.rerun()

    st.divider()
    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if not st.session_state.messages:
    st.session_state.messages.append(
        {
            "role": "assistant",
            "is_greeting": True,
            "content": (
                "Hey... welcome in. Take a breath, watch the waterfall cascade on the right, and turn on "
                "some ocean waves or soft rain in the sidebar if you'd like. Whether you want to vent about "
                "a heavy day, sort through something on your mind, or just want company—I'm right here. "
                "How are you feeling right now?"
            ),
        }
    )

for msg in st.session_state.messages:
    avatar = "🌺" if msg["role"] == "assistant" else "✨"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])

st.caption("Need a starting point? Tap one:")
q1, q2, q3 = st.columns(3)
quick_prompt = None
if q1.button("🌊 I'm feeling overwhelmed", use_container_width=True):
    quick_prompt = "I'm feeling really overwhelmed right now and just need someone to talk to."
if q2.button("🌙 Can't sleep / lonely", use_container_width=True):
    quick_prompt = "I'm up late feeling lonely and my brain won't turn off."
if q3.button("🎲 Play a calming game", use_container_width=True):
    quick_prompt = "Can we play a fun, low-stress mini-game right here in chat to distract me?"

user_input = st.chat_input("Speak with Lexi...")
prompt = quick_prompt or user_input

if prompt:
    safety_level = check_safety_level(prompt)

    if safety_level == "CRISIS":
        st.session_state.crisis_locked = True
        st.rerun()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="✨"):
        st.write(prompt)

    if safety_level == "DISTRESS":
        render_distress_grounding()

    system_instruction = get_lexicare_identity(st.session_state.chat_mode, safety_level)

    with st.chat_message("assistant", avatar="🌺"):
        with st.spinner("Lexi is listening..."):
            reply = generate_lexi_reply(system_instruction, st.session_state.messages)
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

            if st.session_state.voice_enabled:
                speak_text(reply, st.session_state.chat_mode, safety_level)
