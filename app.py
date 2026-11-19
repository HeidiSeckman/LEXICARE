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
if "ambient_scene" not in st.session_state:
    st.session_state.ambient_scene = "Ocean Waves"

# --- Luxury Cancun / Hawaii Twilight Spa Theme & Animated Backdrop ---
st.markdown(
    """
    <style>
    @keyframes oceanTide {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    @keyframes rainFall {
        0% { background-position: 0 0; }
        100% { background-position: -60px 600px; }
    }

    @keyframes waveRise {
        0%, 100% { transform: translateY(0px) scaleY(1); opacity: 0.35; }
        50% { transform: translateY(-18px) scaleY(1.06); opacity: 0.6; }
    }

    /* Deep Twilight Tropical Ocean Base */
    .stApp {
        background: linear-gradient(-45deg, #07191e, #0d2e36, #113c42, #092229);
        background-size: 300% 300%;
        animation: oceanTide 18s ease infinite;
        color: #f3f7f5 !important;
    }

    /* Animated Ambient Overlay (Waves & Gentle Rain Shimmer) */
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        background-image:
            radial-gradient(ellipse at 20% 85%, rgba(45, 168, 158, 0.22) 0%, transparent 55%),
            radial-gradient(ellipse at 80% 20%, rgba(212, 175, 118, 0.12) 0%, transparent 50%),
            repeating-linear-gradient(
                105deg,
                rgba(255, 255, 255, 0.0) 0px,
                rgba(255, 255, 255, 0.0) 28px,
                rgba(165, 225, 220, 0.045) 29px,
                rgba(255, 255, 255, 0.0) 30px
            );
        background-size: 100% 100%, 100% 100%, 240px 600px;
        animation: rainFall 14s linear infinite;
    }

    /* Force High-Contrast Ivory Typography Across Every Streamlit Element */
    .stApp p, .stApp span, .stApp label, .stApp li, .stApp div,
    .stMarkdown, .stCaption, [data-testid="stCaptionContainer"] {
        color: #eef5f2 !important;
    }

    .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
        color: #ffffff !important;
        font-weight: 600;
    }

    [data-testid="stHeader"] {
        background: rgba(7, 25, 30, 0.45) !important;
        backdrop-filter: blur(10px);
    }

    /* Luxury Spa Frosted Dark-Teal Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(8, 28, 34, 0.88) !important;
        backdrop-filter: blur(18px);
        border-right: 1px solid rgba(114, 196, 184, 0.22);
    }

    /* Hero Spa Banner */
    .lexi-hero {
        position: relative;
        z-index: 1;
        background: linear-gradient(135deg, rgba(14, 46, 54, 0.86), rgba(9, 31, 38, 0.92));
        backdrop-filter: blur(18px);
        border: 1px solid rgba(124, 206, 192, 0.32);
        border-radius: 22px;
        padding: 1.5rem 1.75rem;
        text-align: center;
        margin-bottom: 1.1rem;
        box-shadow: 0 14px 38px rgba(0, 0, 0, 0.35);
    }

    .lexi-hero h1 {
        margin: 0;
        font-size: 2.25rem;
        letter-spacing: -0.02em;
        color: #ffffff !important;
    }

    .lexi-badge {
        display: inline-block;
        margin-top: 0.45rem;
        padding: 0.25rem 0.85rem;
        border-radius: 999px;
        background: rgba(86, 186, 172, 0.16);
        border: 1px solid rgba(124, 206, 192, 0.35);
        color: #b8ece3 !important;
        font-size: 0.84rem;
        letter-spacing: 0.04em;
    }

    /* Chat Message Frosted Cards */
    [data-testid="stChatMessage"] {
        background: rgba(12, 40, 48, 0.84) !important;
        backdrop-filter: blur(14px);
        border: 1px solid rgba(124, 206, 192, 0.24);
        border-radius: 18px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }

    /* Containers & Expanders */
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stExpander"] {
        background: rgba(11, 37, 44, 0.85) !important;
        border: 1px solid rgba(124, 206, 192, 0.25) !important;
        border-radius: 16px !important;
    }

    /* Buttons (Warm Seafoam & Champagne Gold Accents) */
    .stButton > button {
        border-radius: 12px !important;
        border: 1px solid rgba(124, 206, 192, 0.38) !important;
        background: rgba(18, 58, 68, 0.85) !important;
        color: #f3f7f5 !important;
        font-weight: 500 !important;
        transition: all 0.22s ease;
    }

    .stButton > button:hover {
        background: rgba(42, 118, 122, 0.92) !important;
        border-color: #9fe3d8 !important;
        color: #ffffff !important;
        transform: translateY(-1px);
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2b8a82, #1f6b69) !important;
        border: 1px solid #8ce0d2 !important;
        color: #ffffff !important;
    }

    /* Text Inputs, Text Areas & Chat Box */
    textarea, input, [data-testid="stChatInput"] textarea {
        background-color: rgba(8, 28, 34, 0.92) !important;
        color: #f4f8f6 !important;
        border: 1px solid rgba(124, 206, 192, 0.35) !important;
        border-radius: 12px !important;
    }

    [data-baseweb="select"] > div {
        background-color: rgba(8, 28, 34, 0.92) !important;
        color: #f4f8f6 !important;
        border-color: rgba(124, 206, 192, 0.35) !important;
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


st.markdown(
    """
    <div class="lexi-hero">
        <h1>🌺 LexiCare</h1>
        <div class="lexi-badge">POWERED BY LEXITECH • 24/7 SANCTUARY & AI COMPANION</div>
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
        st.subheader("Take a slow breath. Welcome to your sanctuary.")
        st.write(
            "LexiCare is a peaceful, judgment-free retreat to talk through your day, "
            "unwind to ocean waves or rain, and reset whenever life feels heavy."
        )
        st.info(
            "**Before stepping inside, please confirm:**\n"
            "- Lexi is an AI companion—not a licensed therapist, doctor, or counselor.\n"
            "- Lexi cannot diagnose conditions or automatically call 911 for you.\n"
            "- If you are ever in immediate danger, tap **Human Support** at the top or call **988** / **911**."
        )
        agreed = st.checkbox(
            "I understand that LexiCare is an AI wellness companion and not medical or therapy care."
        )
        if st.button("Enter Sanctuary", type="primary", disabled=not agreed):
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
            "content": (
                "Hey... welcome in. Take a breath, settle into the quiet, and turn on some ocean waves "
                "or soft rain in the sidebar if you'd like. Whether you want to vent about a heavy day, "
                "sort through something on your mind, or just want company—I'm right here. How are you feeling right now?"
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

# --- Live Animated Ocean Tide Floor ---
st.markdown(
    """
    <div style="position: fixed; bottom: 0; left: 0; width: 100%; height: 95px; pointer-events: none; z-index: 0; overflow: hidden; opacity: 0.45;">
        <svg viewBox="0 0 1440 120" preserveAspectRatio="none" style="width: 200%; height: 100%; animation: tideSlide 16s linear infinite;">
            <path d="M0,45 C360,110 720,-15 1080,55 C1260,90 1350,70 1440,45 L1440,120 L0,120 Z" fill="rgba(56, 178, 172, 0.35)"></path>
            <path d="M0,70 C320,10 680,115 1040,55 C1240,25 1360,65 1440,70 L1440,120 L0,120 Z" fill="rgba(129, 230, 217, 0.22)"></path>
        </svg>
    </div>
    <style>
    @keyframes tideSlide {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)
