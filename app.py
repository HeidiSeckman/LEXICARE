import asyncio
import io
import time
import wave
import edge_tts
from google import genai
from google.genai import types
import numpy as np
import streamlit as st
from lexi_identity import get_lexicare_identity
from safety_shield import (
    check_safety_level,
    render_crisis_card,
    render_distress_grounding,
    render_safety_header,
)

st.set_page_config(
    page_title="LexiCare | Powered by LexiTech",
    page_icon="🌿",
    layout="centered",
)

st.markdown(
    """
    <style>
    @keyframes calmDrift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .stApp {
        background: linear-gradient(-45deg, #eef5f0, #e3eff5, #f5f1ea, #e4efe9);
        background-size: 400% 400%;
        animation: calmDrift 22s ease infinite;
        color: #1f2d27;
    }
    [data-testid="stHeader"] { background: rgba(255, 255, 255, 0.0); }
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.72);
        backdrop-filter: blur(14px);
        border-right: 1px solid rgba(110, 145, 130, 0.18);
    }
    .lexi-hero {
        background: rgba(255, 255, 255, 0.72);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(110, 145, 130, 0.22);
        border-radius: 20px;
        padding: 1.35rem 1.5rem;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 8px 28px rgba(45, 75, 62, 0.06);
    }
    .lexi-hero h1 { margin: 0; font-size: 2.15rem; color: #1e352b; letter-spacing: -0.02em; }
    .lexi-sub { color: #4f6b5e; font-size: 0.92rem; margin-top: 0.25rem; }
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.76);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(110, 145, 130, 0.18);
        border-radius: 16px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.65rem;
        box-shadow: 0 4px 14px rgba(45, 75, 62, 0.04);
    }
    .stButton > button {
        border-radius: 12px;
        border: 1px solid rgba(92, 132, 114, 0.28);
        background: rgba(255, 255, 255, 0.82);
        color: #1e352b;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: #dfeee6;
        border-color: #5c8472;
        color: #162920;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def generate_nature_sound(sound_type: str, duration_sec: int = 25) -> bytes:
    sample_rate = 22050
    n_samples = sample_rate * duration_sec
    rng = np.random.default_rng(42)
    white = rng.standard_normal(n_samples)

    b = np.cumsum(white)
    b = b - np.mean(b)
    b = b / (np.max(np.abs(b)) + 1e-6)

    kernel_size = 35 if sound_type == "Soft Rain" else 90
    kernel = np.ones(kernel_size) / kernel_size
    smooth_noise = np.convolve(white, kernel, mode="same")
    smooth_noise = smooth_noise / (np.max(np.abs(smooth_noise)) + 1e-6)

    t = np.linspace(0, duration_sec, n_samples, endpoint=False)

    if sound_type == "Ocean Waves":
        swell = 0.45 + 0.55 * (0.5 * (1 + np.sin(2 * np.pi * t / 8.5)))
        audio = (0.65 * b + 0.35 * smooth_noise) * swell
    elif sound_type == "Forest Waterfall":
        gentle_flow = 0.88 + 0.12 * np.sin(2 * np.pi * t / 5.0)
        audio = (0.55 * b + 0.45 * smooth_noise) * gentle_flow
    else:
        rain_patter = np.convolve(white, np.ones(12) / 12, mode="same")
        rain_patter = rain_patter / (np.max(np.abs(rain_patter)) + 1e-6)
        audio = 0.35 * b + 0.45 * smooth_noise + 0.20 * rain_patter

    fade_len = int(sample_rate * 1.5)
    audio[:fade_len] *= np.linspace(0, 1, fade_len)
    audio[-fade_len:] *= np.linspace(1, 0, fade_len)

    pcm = np.int16(np.clip(audio * 0.35, -1.0, 1.0) * 32767)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


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
    <div class="lexi-hero">
        <h1>🌿 LexiCare</h1>
        <div class="lexi-sub">Powered by LexiTech • Your 24/7 Safe Space & AI Companion</div>
    </div>
    """,
    unsafe_allow_html=True,
)

render_safety_header()

if st.session_state.get("crisis_locked", False):
    render_crisis_card()
    st.stop()

if not st.session_state.accepted_terms:
    with st.container(border=True):
        st.subheader("Take a deep breath. Welcome to LexiCare.")
        st.write(
            "LexiCare is a peaceful, judgment-free space to talk through your day, unwind, "
            "or find quick calming activities whenever life feels heavy."
        )
        st.info(
            "**Before we start, please confirm:**\n"
            "- Lexi is an AI companion—not a licensed therapist, doctor, or counselor.\n"
            "- Lexi cannot diagnose conditions or automatically call 911 for you.\n"
            "- If you are ever in immediate danger, please use the **Human Support** button at the top or call **988** / **911**."
        )
        agreed = st.checkbox(
            "I understand that LexiCare is an AI wellness companion and not medical or therapy care."
        )
        if st.button("Enter LexiCare", type="primary", disabled=not agreed):
            st.session_state.accepted_terms = True
            st.rerun()
    st.stop()
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
    recent_messages = messages[-8:]

    gemini_key = st.secrets.get("GEMINI_API_KEY", "")
    if gemini_key:
        try:
            client = genai.Client(api_key=gemini_key)
            history_text = "\n".join(
                f"{m['role'].upper()}: {m['content']}" for m in recent_messages
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=history_text,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.75,
                ),
            )
            if response.text:
                return response.text
        except Exception:
            pass

    groq_key = st.secrets.get("GROQ_API_KEY", "")
    if groq_key:
        try:
            from groq import Groq

            groq_client = Groq(api_key=groq_key)
            groq_messages = [{"role": "system", "content": system_instruction}]
            for m in recent_messages:
                groq_messages.append({"role": m["role"], "content": m["content"]})

            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=groq_messages,
                temperature=0.75,
            )
            reply_text = completion.choices[0].message.content
            if reply_text:
                return reply_text
        except Exception:
            pass

    return (
        "Hey, I'm still right here with you—my connection just blinked for a second. "
        "Go ahead and send that one more time."
    )


with st.sidebar:
    st.header("🎧 Calming Soundscapes")
    ambient_choice = st.selectbox(
        "Background Nature Audio",
        ["Off", "Soft Rain", "Ocean Waves", "Forest Waterfall"],
    )
    if ambient_choice != "Off":
        sound_bytes = generate_nature_sound(ambient_choice)
        st.audio(sound_bytes, format="audio/wav", loop=True, autoplay=True)
        st.caption(f"Looping {ambient_choice.lower()} softly in the background.")

    st.divider()
    st.header("🌿 LexiCare Toolkit")
    st.session_state.chat_mode = st.radio(
        "How should Lexi respond right now?",
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
        placeholder.success("Nice job. Notice how your shoulders feel right now.")

    st.divider()
    st.subheader("🗑️ Brain Dump Shredder")
    worry = st.text_area(
        "Type a stress or thought you want to let go of:",
        placeholder="Write it here, then shred it...",
        height=80,
    )
    if st.button("Shred This Thought", use_container_width=True):
        if worry.strip():
            st.toast("Shredded and cleared from your space. 🍃")
            st.rerun()

    st.divider()
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if not st.session_state.messages:
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": (
                "Hey... I'm Lexi. Take a second, settle in, and turn on some rain or ocean waves "
                "in the sidebar if you want. Whether you need to vent about a rough day, sort through "
                "something on your mind, or just want company—I'm right here. What's going on today?"
            ),
        }
    )

for msg in st.session_state.messages:
    avatar = "🌿" if msg["role"] == "assistant" else "🧑"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])

st.caption("Need a starting point? Tap one:")
q1, q2, q3 = st.columns(3)
quick_prompt = None
if q1.button("😔 I'm feeling overwhelmed", use_container_width=True):
    quick_prompt = "I'm feeling really overwhelmed right now and just need someone to talk to."
if q2.button("🌙 Can't sleep / lonely", use_container_width=True):
    quick_prompt = "I'm up late feeling lonely and my brain won't turn off."
if q3.button("🎲 Play a calming game", use_container_width=True):
    quick_prompt = "Can we play a fun, low-stress mini-game right here in chat to distract me?"

user_input = st.chat_input("Tell Lexi anything...")
prompt = quick_prompt or user_input

if prompt:
    safety_level = check_safety_level(prompt)

    if safety_level == "CRISIS":
        st.session_state.crisis_locked = True
        st.rerun()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.write(prompt)

    if safety_level == "DISTRESS":
        render_distress_grounding()

    system_instruction = get_lexicare_identity(st.session_state.chat_mode, safety_level)

    with st.chat_message("assistant", avatar="🌿"):
        with st.spinner("Lexi is listening..."):
            reply = generate_lexi_reply(system_instruction, st.session_state.messages)
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

            if st.session_state.voice_enabled:
                speak_text(reply, st.session_state.chat_mode, safety_level)
