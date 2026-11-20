import os
import io
import wave
import time
import asyncio
import numpy as np
import streamlit as st
import edge_tts
from google import genai
from google.genai import types
from groq import Groq

from safety_shield import (
    check_safety_level,
    render_safety_header,
    render_crisis_card,
    render_distress_grounding,
)
from lexi_identity import get_lexicare_identity

LOTUS = "\U0001fab7"
SPARKLE = "\u2728"

st.set_page_config(
    page_title="LexiCare | Powered by LexiTech",
    page_icon=LOTUS,
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <link rel="preconnect" href="https://googleapis.com">
    <link rel="preconnect" href="https://gstatic.com" crossorigin>
    <link href="https://googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">

    <style>
    :root {
        --glass-card: rgba(11, 52, 60, 0.88);
        --gold-champagne: #f5e2c4;
        --seafoam: #a8f5e6;
        --text-main: #fbfefd;
    }

    html, body, [data-testid="stAppViewContainer"], .stApp {
        background: radial-gradient(circle at 22% 12%, #1d6d78 0%, #0f454e 45%, #082930 100%) !important;
        color: var(--text-main) !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        overflow-x: hidden;
    }

    [data-testid="stIconMaterial"], .material-symbols-rounded {
        font-family: 'Material Symbols Rounded' !important;
        font-weight: normal !important;
        font-style: normal !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-block !important;
        white-space: nowrap !important;
        direction: ltr !important;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
        z-index: 30 !important;
    }

    /* Sunlit Beachfront Lagoon Sidebar (Never Black) */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(180deg, rgba(22, 88, 97, 0.92) 0%, rgba(13, 58, 66, 0.95) 55%, rgba(10, 44, 51, 0.97) 100%) !important;
        backdrop-filter: blur(22px) !important;
        border-right: 1px solid rgba(245, 226, 196, 0.28) !important;
        box-shadow: 8px 0 32px rgba(4, 24, 29, 0.35) !important;
        z-index: 30 !important;
    }

    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #f7fbfb !important;
    }

    .main .block-container,
    [data-testid="stAppViewBlockContainer"],
    [data-testid="stBottom"],
    [data-testid="stBottomBlockContainer"] {
        position: relative !important;
        z-index: 25 !important;
    }

    h1, h2, h3, .spa-serif {
        font-family: 'Cormorant Garamond', Georgia, serif !important;
        letter-spacing: 0.02em !important;
        color: var(--gold-champagne) !important;
    }

    p, div, span, label, input, textarea, button {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .sanctuary-bg-layer {
        position: fixed;
        inset: 0;
        z-index: 1;
        pointer-events: none;
        overflow: hidden;
    }

    .waterfall-column {
        position: fixed;
        top: 0;
        right: 0;
        width: 175px;
        height: 100vh;
        z-index: 1;
        pointer-events: none;
        background: linear-gradient(90deg, rgba(168, 245, 230, 0) 0%, rgba(168, 245, 230, 0.14) 28%, rgba(225, 253, 250, 0.28) 68%, rgba(245, 226, 196, 0.22) 100%);
        overflow: hidden;
    }

    .wf-layer-1 {
        position: absolute;
        top: -240px;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: repeating-linear-gradient(90deg, transparent 0px, transparent 8px, rgba(235, 255, 253, 0.28) 11px, transparent 14px, rgba(245, 226, 196, 0.20) 20px, transparent 25px);
        background-size: 100% 240px;
        animation: wfDropSlow 2.3s linear infinite;
    }

    .wf-layer-2 {
        position: absolute;
        top: -180px;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: repeating-linear-gradient(90deg, transparent 0px, rgba(255, 255, 255, 0.42) 2px, transparent 5px, transparent 15px);
        background-size: 100% 180px;
        animation: wfDropFast 1.25s linear infinite;
    }

    @keyframes wfDropSlow {
        0% { transform: translateY(0px); }
        100% { transform: translateY(240px); }
    }

    @keyframes wfDropFast {
        0% { transform: translateY(0px); }
        100% { transform: translateY(180px); }
    }

    .waterfall-mist {
        position: fixed;
        bottom: 0;
        right: 0;
        width: 300px;
        height: 130px;
        background: radial-gradient(ellipse at 80% 100%, rgba(230, 255, 252, 0.48) 0%, rgba(168, 245, 230, 0.18) 50%, transparent 78%);
        filter: blur(10px);
        animation: mistBreathe 3.5s ease-in-out infinite;
    }

    .lagoon-wave {
        position: fixed;
        bottom: -10px;
        left: 0;
        width: 200%;
        height: 52px;
        background: linear-gradient(180deg, rgba(168, 245, 230, 0.18), rgba(245, 226, 196, 0.14));
        border-top: 1px solid rgba(245, 226, 196, 0.35);
        border-radius: 50% 50% 0 0;
        animation: lagoonRoll 8s ease-in-out infinite alternate;
    }

    @keyframes mistBreathe {
        0%, 100% { opacity: 0.75; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.08); }
    }

    @keyframes lagoonRoll {
        0% { transform: translateX(0%) translateY(0px); }
        100% { transform: translateX(-25%) translateY(-6px); }
    }
    .golden-lotus {
        position: absolute;
        opacity: 0.48;
        filter: drop-shadow(0 0 16px rgba(250, 220, 155, 0.95)) drop-shadow(0 0 36px rgba(240, 195, 110, 0.72));
        animation: lotusDrift 14s ease-in-out infinite;
    }
    .lotus-1 { top: 6%; left: 2%; width: 118px; animation-delay: 0s; }
    .lotus-2 { top: 28%; left: 4%; width: 92px; animation-delay: -3s; }
    .lotus-3 { top: 54%; left: 1.5%; width: 128px; animation-delay: -6s; }
    .lotus-4 { bottom: 10%; left: 3.5%; width: 102px; animation-delay: -9s; }
    .lotus-5 { top: 8%; right: 13%; width: 110px; animation-delay: -2s; }
    .lotus-6 { top: 34%; right: 15%; width: 88px; animation-delay: -5s; }
    .lotus-7 { top: 60%; right: 12.5%; width: 122px; animation-delay: -8s; }
    .lotus-8 { bottom: 12%; right: 14%; width: 98px; animation-delay: -11s; }

    @keyframes lotusDrift {
        0%, 100% { transform: translateY(0px) rotate(-3deg) scale(1); }
        50% { transform: translateY(-18px) rotate(5deg) scale(1.06); }
    }

    .lexicare-hero {
        position: relative;
        z-index: 25;
        background: linear-gradient(145deg, rgba(16, 68, 78, 0.92), rgba(10, 46, 54, 0.95));
        backdrop-filter: blur(22px);
        border: 1px solid rgba(245, 226, 196, 0.42);
        border-radius: 26px;
        padding: 2rem 1.8rem 1.8rem;
        text-align: center;
        box-shadow: 0 20px 50px rgba(4, 24, 30, 0.45), inset 0 1px 0 rgba(255, 248, 235, 0.25);
        margin-bottom: 1rem;
    }

    .lexicare-title {
        font-family: 'Cormorant Garamond', Georgia, serif !important;
        font-size: 3.15rem !important;
        font-weight: 600 !important;
        color: #fbf0dc !important;
        margin: 0 !important;
        line-height: 1.08 !important;
        text-shadow: 0 2px 18px rgba(245, 226, 196, 0.35);
    }

    .lexicare-pill {
        display: inline-block;
        margin-top: 0.75rem;
        padding: 0.38rem 1.15rem;
        border-radius: 999px;
        background: rgba(168, 245, 230, 0.14);
        border: 1px solid rgba(245, 226, 196, 0.38);
        color: var(--gold-champagne);
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.14em;
        text-transform: uppercase;
    }

    [data-testid="stChatMessage"], [data-testid="stExpander"] {
        position: relative !important;
        z-index: 25 !important;
        background: var(--glass-card) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(245, 226, 196, 0.30) !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 28px rgba(4, 24, 30, 0.32) !important;
    }

    [data-testid="stChatInput"] {
        position: relative !important;
        z-index: 30 !important;
        background: rgba(12, 54, 63, 0.96) !important;
        border: 1px solid rgba(245, 226, 196, 0.42) !important;
        border-radius: 18px !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, rgba(28, 102, 112, 0.92), rgba(16, 68, 78, 0.95)) !important;
        color: #fbf0dc !important;
        border: 1px solid rgba(245, 226, 196, 0.42) !important;
        border-radius: 14px !important;
    }
    </style>

    <div class="sanctuary-bg-layer">
        <svg class="golden-lotus lotus-1" viewBox="0 0 120 120" fill="none"><path d="M60 12C69 34 73 52 60 74C47 52 51 34 60 12Z" fill="#fbe4b4" fill-opacity="0.92"/><path d="M60 74C40 57 30 42 28 24C47 34 55 51 60 74Z" fill="#f5e2c4" fill-opacity="0.78"/><path d="M60 74C80 57 90 42 92 24C73 34 65 51 60 74Z" fill="#f5e2c4" fill-opacity="0.78"/><path d="M60 77C34 70 18 57 12 42C33 45 47 57 60 77Z" fill="#f5e2c4" fill-opacity="0.62"/><path d="M60 77C86 70 102 57 108 42C87 45 73 57 60 77Z" fill="#f5e2c4" fill-opacity="0.62"/></svg>
        <svg class="golden-lotus lotus-2" viewBox="0 0 120 120" fill="none"><path d="M60 12C69 34 73 52 60 74C47 52 51 34 60 12Z" fill="#fbe4b4" fill-opacity="0.9"/><path d="M60 74C40 57 30 42 28 24C47 34 55 51 60 74Z" fill="#f5e2c4" fill-opacity="0.75"/><path d="M60 74C80 57 90 42 92 24C73 34 65 51 60 74Z" fill="#f5e2c4" fill-opacity="0.75"/></svg>
        <svg class="golden-lotus lotus-3" viewBox="0 0 120 120" fill="none"><path d="M60 12C69 34 73 52 60 74C47 52 51 34 60 12Z" fill="#fbe4b4" fill-opacity="0.92"/><path d="M60 74C40 57 30 42 28 24C47 34 55 51 60 74Z" fill="#f5e2c4" fill-opacity="0.78"/><path d="M60 74C80 57 90 42 92 24C73 34 65 51 60 74Z" fill="#f5e2c4" fill-opacity="0.78"/><path d="M60 77C34 70 18 57 12 42C33 45 47 57 60 77Z" fill="#f5e2c4" fill-opacity="0.62"/><path d="M60 77C86 70 102 57 108 42C87 45 73 57 60 77Z" fill="#f5e2c4" fill-opacity="0.62"/></svg>
        <svg class="golden-lotus lotus-4" viewBox="0 0 120 120" fill="none"><path d="M60 12C69 34 73 52 60 74C47 52 51 34 60 12Z" fill="#fbe4b4" fill-opacity="0.9"/><path d="M60 74C40 57 30 42 28 24C47 34 55 51 60 74Z" fill="#f5e2c4" fill-opacity="0.75"/><path d="M60 74C80 57 90 42 92 24C73 34 65 51 60 74Z" fill="#f5e2c4" fill-opacity="0.75"/></svg>
        <svg class="golden-lotus lotus-5" viewBox="0 0 120 120" fill="none"><path d="M60 12C69 34 73 52 60 74C47 52 51 34 60 12Z" fill="#fbe4b4" fill-opacity="0.92"/><path d="M60 74C40 57 30 42 28 24C47 34 55 51 60 74Z" fill="#f5e2c4" fill-opacity="0.78"/><path d="M60 74C80 57 90 42 92 24C73 34 65 51 60 74Z" fill="#f5e2c4" fill-opacity="0.78"/></svg>
        <svg class="golden-lotus lotus-6" viewBox="0 0 120 120" fill="none"><path d="M60 12C69 34 73 52 60 74C47 52 51 34 60 12Z" fill="#fbe4b4" fill-opacity="0.9"/><path d="M60 74C40 57 30 42 28 24C47 34 55 51 60 74Z" fill="#f5e2c4" fill-opacity="0.75"/><path d="M60 74C80 57 90 42 92 24C73 34 65 51 60 74Z" fill="#f5e2c4" fill-opacity="0.75"/></svg>
        <svg class="golden-lotus lotus-7" viewBox="0 0 120 120" fill="none"><path d="M60 12C69 34 73 52 60 74C47 52 51 34 60 12Z" fill="#fbe4b4" fill-opacity="0.92"/><path d="M60 74C40 57 30 42 28 24C47 34 55 51 60 74Z" fill="#f5e2c4" fill-opacity="0.78"/><path d="M60 74C80 57 90 42 92 24C73 34 65 51 60 74Z" fill="#f5e2c4" fill-opacity="0.78"/><path d="M60 77C34 70 18 57 12 42C33 45 47 57 60 77Z" fill="#f5e2c4" fill-opacity="0.62"/><path d="M60 77C86 70 102 57 108 42C87 45 73 57 60 77Z" fill="#f5e2c4" fill-opacity="0.62"/></svg>
        <svg class="golden-lotus lotus-8" viewBox="0 0 120 120" fill="none"><path d="M60 12C69 34 73 52 60 74C47 52 51 34 60 12Z" fill="#fbe4b4" fill-opacity="0.9"/><path d="M60 74C40 57 30 42 28 24C47 34 55 51 60 74Z" fill="#f5e2c4" fill-opacity="0.75"/><path d="M60 74C80 57 90 42 92 24C73 34 65 51 60 74Z" fill="#f5e2c4" fill-opacity="0.75"/></svg>

        <div class="waterfall-column">
            <div class="wf-layer-1"></div>
            <div class="wf-layer-2"></div>
        </div>
        <div class="waterfall-mist"></div>
        <div class="lagoon-wave"></div>
    </div>
    """,
    unsafe_allow_html=True,
)
@st.cache_data(show_spinner=False)
def generate_soundscape_wav(sound_type: str) -> bytes:
    sample_rate = 22050
    duration = 12.0
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    rng = np.random.default_rng(42)

    if sound_type == "Ocean Waves":
        noise = rng.normal(0, 1, size=t.shape)
        surf = np.convolve(noise, np.ones(65) / 65.0, mode="same")
        swell = 0.55 + 0.45 * np.sin(2 * np.pi * (1.0 / 6.0) * t - np.pi / 2)
        wave_audio = surf * swell * 2.8
    elif sound_type == "Soft Rain":
        noise = rng.normal(0, 1, size=t.shape)
        rain = np.convolve(noise, np.ones(18) / 18.0, mode="same")
        droplets = (rng.random(size=t.shape) > 0.9965).astype(float) * rng.normal(0, 0.45, size=t.shape)
        wave_audio = (rain * 1.3 + droplets) * 0.65
    else:
        noise = rng.normal(0, 1, size=t.shape)
        low_rumble = np.convolve(noise, np.ones(90) / 90.0, mode="same") * 2.2
        mist_hiss = np.convolve(noise, np.ones(14) / 14.0, mode="same") * 0.45
        wave_audio = (low_rumble + mist_hiss) * 0.75

    fade = int(sample_rate * 0.8)
    wave_audio[:fade] *= np.linspace(0, 1, fade)
    wave_audio[-fade:] *= np.linspace(1, 0, fade)

    max_val = np.max(np.abs(wave_audio)) or 1.0
    pcm = np.int16((wave_audio / max_val) * 26000)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


async def _synthesize_ava_async(text: str, rate: str, pitch: str) -> bytes:
    communicate = edge_tts.Communicate(
        text=text,
        voice="en-US-AvaMultilingualNeural",
        rate=rate,
        pitch=pitch,
    )
    chunks = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.extend(chunk["data"])
    return bytes(chunks)


def generate_lexi_voice(text: str, chat_mode: str):
    clean_text = text.replace("*", "").replace("#", "").strip()
    if not clean_text:
        return None
    if len(clean_text) > 900:
        clean_text = clean_text[:900] + "..."

    if chat_mode == "Just Listen (Vent)":
        rate, pitch = "-6%", "-2Hz"
    elif chat_mode == "Distract Me / Play a Game":
        rate, pitch = "+2%", "+1Hz"
    else:
        rate, pitch = "-2%", "+0Hz"

    try:
        return asyncio.run(_synthesize_ava_async(clean_text, rate, pitch))
    except Exception:
        return None


def get_lexi_response(user_prompt: str, messages: list, chat_mode: str, safety_level: str) -> str:
    system_instruction = get_lexicare_identity(chat_mode=chat_mode, safety_level=safety_level)
    prior_turns = messages[1:-1] if len(messages) > 2 else []

    gemini_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
    if gemini_key:
        try:
            client = genai.Client(api_key=gemini_key)
            contents = []
            for msg in prior_turns[-12:]:
                role = "user" if msg["role"] == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)]))

            for model_name in ("gemini-2.5-flash", "gemini-2.0-flash"):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.65,
                            max_output_tokens=700,
                        ),
                    )
                    if response and response.text:
                        return response.text.strip()
                except Exception:
                    continue
        except Exception:
            pass

    groq_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
    if groq_key:
        try:
            groq_client = Groq(api_key=groq_key)
            available_models = groq_client.models.list()
            llama_models = [
                m.id
                for m in available_models.data
                if "llama" in m.id.lower() and "guard" not in m.id.lower() and "vision" not in m.id.lower()
            ]
            chosen_model = llama_models[0] if llama_models else "llama-3.3-70b-versatile"

            groq_messages = [{"role": "system", "content": system_instruction}]
            for msg in prior_turns[-12:]:
                groq_messages.append({"role": msg["role"], "content": msg["content"]})
            groq_messages.append({"role": "user", "content": user_prompt})

            completion = groq_client.chat.completions.create(
                model=chosen_model,
                messages=groq_messages,
                temperature=0.65,
                max_tokens=700,
            )
            reply = completion.choices[0].message.content
            if reply:
                return reply.strip()
        except Exception:
            pass

    return (
        "I am right here with you in the sanctuary. My cloud connection flickered for just a moment—"
        "take a slow breath and send that again whenever you are ready."
    )
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hey... welcome in. Take a breath, watch the waterfall cascade behind us, "
                "and turn on some ocean waves or soft rain in the sidebar if you'd like. "
                "Whether you want to vent, work through something on your mind, or just be distracted "
                "for a little while, I'm right here."
            ),
        }
    ]

if "crisis_locked" not in st.session_state:
    st.session_state.crisis_locked = False

if "latest_voice_bytes" not in st.session_state:
    st.session_state.latest_voice_bytes = None


with st.sidebar:
    st.markdown(f"## {LOTUS} Sanctuary Controls")

    chat_mode = st.selectbox(
        "How can LEXI support you right now?",
        options=[
            "Just Listen (Vent)",
            "Help Me Problem-Solve",
            "Distract Me / Play a Game",
        ],
        index=0,
    )

    voice_enabled = st.toggle("LEXI Voice Replies (Ava Neural)", value=True)

    st.markdown("---")
    st.markdown("### Ambient Soundscapes")
    sound_choice = st.selectbox(
        "Choose a soothing backdrop",
        options=["None", "Ocean Waves", "Soft Rain", "Forest Waterfall"],
        index=0,
    )
    if sound_choice != "None":
        st.audio(generate_soundscape_wav(sound_choice), format="audio/wav", loop=True)

    st.markdown("---")
    st.markdown("### 60-Second Calm Reset")
    if st.button("Start 60s Guided Breath", use_container_width=True):
        breath_box = st.empty()
        cycles = [
            ("Inhale slowly through your nose...", 4),
            ("Hold gently at the top...", 4),
            ("Exhale long and soft...", 6),
        ]
        for _ in range(4):
            for label, secs in cycles:
                for sec in range(secs, 0, -1):
                    breath_box.info(f"**{label}** ({sec}s)")
                    time.sleep(1)
        breath_box.success("Beautiful. Notice your shoulders dropping.")

    st.markdown("---")
    st.markdown("### Worry Release")
    worry_text = st.text_area(
        "Write down a heavy thought to let go of:",
        placeholder="Type anything weighing on you, then dissolve it into the lagoon...",
        height=85,
    )
    if st.button("Dissolve Into the Water", use_container_width=True):
        if worry_text.strip():
            st.toast("Released. Watching it drift away with the tide...", icon=LOTUS)

    st.markdown("---")
    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.messages = [st.session_state.messages[0]]
        st.session_state.latest_voice_bytes = None
        st.rerun()


st.markdown(
    f"""
    <div class="lexicare-hero">
        <h1 class="lexicare-title">{LOTUS} LexiCare</h1>
        <div class="lexicare-pill">Powered by LexiTech &bull; Private Sanctuary &amp; AI Companion</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.components.v1.html(
    """
    <div style="position:relative; width:100%; height:150px; border-radius:22px; overflow:hidden;
                background: radial-gradient(circle at 30% 40%, rgba(25,104,115,0.92), rgba(10,48,56,0.96));
                border: 1px solid rgba(245, 226, 196, 0.38); box-shadow: 0 14px 36px rgba(4,24,30,0.45);">
        <canvas id="orbCanvas" style="width:100%; height:100%; display:block; cursor:crosshair;"></canvas>
        <div style="position:absolute; bottom:10px; right:16px; font-family:'Plus Jakarta Sans',sans-serif;
                    font-size:11px; letter-spacing:0.12em; color:#f5e2c4; opacity:0.88; pointer-events:none;">
            MOVE CURSOR TO GUIDE THE SANCTUARY ORB
        </div>
    </div>
    <script>
        const canvas = document.getElementById('orbCanvas');
        const ctx = canvas.getContext('2d');
        function resize() {
            canvas.width = canvas.offsetWidth * window.devicePixelRatio;
            canvas.height = canvas.offsetHeight * window.devicePixelRatio;
            ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        }
        resize();
        window.addEventListener('resize', resize);

        let targetX = canvas.offsetWidth * 0.28;
        let targetY = canvas.offsetHeight * 0.50;
        let orbX = targetX;
        let orbY = targetY;
        let angle = 0;

        const pearls = Array.from({ length: 22 }, (_, i) => ({
            x: Math.random() * 650,
            y: Math.random() * 150,
            r: 1.4 + Math.random() * 2.8,
            speed: 0.25 + Math.random() * 0.55,
            gold: i % 2 === 0
        }));

        const trail = [];

        canvas.addEventListener('mousemove', (e) => {
            const rect = canvas.getBoundingClientRect();
            targetX = e.clientX - rect.left;
            targetY = e.clientY - rect.top;
            trail.push({ x: targetX, y: targetY, alpha: 0.55, r: 8 });
            if (trail.length > 18) trail.shift();
        });

        function animate() {
            const w = canvas.offsetWidth;
            const h = canvas.offsetHeight;
            ctx.clearRect(0, 0, w, h);
            angle += 0.025;

            orbX += (targetX - orbX) * 0.08;
            orbY += (targetY - orbY) * 0.08;

            pearls.forEach(p => {
                p.y -= p.speed;
                if (p.y < -5) { p.y = h + 5; p.x = Math.random() * w; }
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fillStyle = p.gold ? 'rgba(251, 228, 180, 0.65)' : 'rgba(168, 245, 230, 0.55)';
                ctx.fill();
            });

            trail.forEach(t => {
                t.alpha *= 0.92;
                t.r += 0.35;
                ctx.beginPath();
                ctx.arc(t.x, t.y, t.r, 0, Math.PI * 2);
                ctx.strokeStyle = `rgba(245, 226, 196, ${t.alpha})`;
                ctx.lineWidth = 1.2;
                ctx.stroke();
            });

            const pulse = Math.sin(angle * 1.4) * 5;
            const outerGlow = ctx.createRadialGradient(orbX, orbY, 4, orbX, orbY, 64 + pulse);
            outerGlow.addColorStop(0, 'rgba(255, 253, 248, 0.98)');
            outerGlow.addColorStop(0.25, 'rgba(251, 228, 180, 0.65)');
            outerGlow.addColorStop(0.58, 'rgba(168, 245, 230, 0.28)');
            outerGlow.addColorStop(1, 'rgba(168, 245, 230, 0)');

            ctx.beginPath();
            ctx.arc(orbX, orbY, 64 + pulse, 0, Math.PI * 2);
            ctx.fillStyle = outerGlow;
            ctx.fill();

            ctx.save();
            ctx.translate(orbX, orbY);
            ctx.rotate(angle);
            ctx.beginPath();
            ctx.ellipse(0, 0, 34, 13, 0, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(251, 228, 180, 0.65)';
            ctx.lineWidth = 1.4;
            ctx.stroke();

            ctx.rotate(-angle * 1.8);
            ctx.beginPath();
            ctx.ellipse(0, 0, 28, 11, Math.PI / 3, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(168, 245, 230, 0.60)';
            ctx.lineWidth = 1.2;
            ctx.stroke();
            ctx.restore();

            const sphereGrad = ctx.createRadialGradient(orbX - 5, orbY - 5, 2, orbX, orbY, 18);
            sphereGrad.addColorStop(0, '#ffffff');
            sphereGrad.addColorStop(0.55, '#fbe4b4');
            sphereGrad.addColorStop(1, 'rgba(168, 245, 230, 0.85)');

            ctx.beginPath();
            ctx.arc(orbX, orbY, 18, 0, Math.PI * 2);
            ctx.fillStyle = sphereGrad;
            ctx.fill();

            requestAnimationFrame(animate);
        }
        animate();
    </script>
    """,
    height=160,
)

render_safety_header()

if st.session_state.crisis_locked:
    render_crisis_card()
else:
    for msg in st.session_state.messages:
        avatar = LOTUS if msg["role"] == "assistant" else SPARKLE
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    if st.session_state.latest_voice_bytes and voice_enabled:
        st.audio(st.session_state.latest_voice_bytes, format="audio/mp3", autoplay=True)

    if prompt := st.chat_input("Speak with Lexi..."):
        safety_level = check_safety_level(prompt)
        if safety_level == "CRISIS":
            st.session_state.crisis_locked = True
            st.rerun()

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=SPARKLE):
            st.markdown(prompt)

        if safety_level == "DISTRESS":
            render_distress_grounding()

        with st.chat_message("assistant", avatar=LOTUS):
            with st.spinner("LEXI is listening..."):
                reply = get_lexi_response(
                    user_prompt=prompt,
                    messages=st.session_state.messages,
                    chat_mode=chat_mode,
                    safety_level=safety_level,
                )
                st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

        if voice_enabled:
            voice_data = generate_lexi_voice(reply, chat_mode)
            st.session_state.latest_voice_bytes = voice_data
            if voice_data:
                st.audio(voice_data, format="audio/mp3", autoplay=True)
