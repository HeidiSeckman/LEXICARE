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

from safety_shield import evaluate_safety, render_crisis_banner, render_trusted_person_setup
from lexi_identity import get_lexicare_identity

LOTUS = "\U0001fab7"
SPARKLE = "\u2728"
SOS = "\U0001f198"

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
        --glass-card: rgba(6, 26, 32, 0.92);
        --gold-champagne: #ebd5b3;
        --seafoam: #9ef0e0;
        --text-main: #f5f9f9;
    }

    html, body, [data-testid="stAppViewContainer"], .stApp {
        background: radial-gradient(circle at 20% 15%, #144d56 0%, #09262d 44%, #041216 100%) !important;
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

    [data-testid="stSidebar"] {
        background: rgba(4, 18, 22, 0.96) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(235, 213, 179, 0.18) !important;
        z-index: 30 !important;
    }

    .main .block-container,
    [data-testid="stAppViewBlockContainer"],
    [data-testid="stBottom"],
    [data-testid="stBottomBlockContainer"] {
        position: relative !important;
        z-index: 20 !important;
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

    .golden-lotus {
        position: absolute;
        opacity: 0.26;
        filter: drop-shadow(0 0 18px rgba(235, 213, 179, 0.75)) drop-shadow(0 0 38px rgba(246, 200, 120, 0.45));
        animation: lotusFloat 18s ease-in-out infinite;
    }
    .lotus-1 { top: 7%; left: 5%; width: 135px; animation-delay: 0s; }
    .lotus-2 { top: 42%; left: 10%; width: 105px; opacity: 0.20; animation-delay: -5s; }
    .lotus-3 { bottom: 16%; left: 4%; width: 155px; opacity: 0.24; animation-delay: -9s; }
    .lotus-4 { top: 12%; right: 16%; width: 115px; opacity: 0.22; animation-delay: -3s; }
    .lotus-5 { bottom: 24%; right: 18%; width: 140px; opacity: 0.24; animation-delay: -12s; }

    @keyframes lotusFloat {
        0%, 100% { transform: translateY(0px) rotate(0deg) scale(1); }
        50% { transform: translateY(-16px) rotate(4deg) scale(1.04); }
    }

    .waterfall-column {
        position: fixed;
        top: 0;
        right: 0;
        width: 150px;
        height: 100vh;
        z-index: 1;
        pointer-events: none;
        background: linear-gradient(90deg, rgba(158, 240, 224, 0) 0%, rgba(158, 240, 224, 0.08) 30%, rgba(215, 250, 248, 0.20) 68%, rgba(235, 213, 179, 0.14) 100%);
        overflow: hidden;
    }

    .waterfall-stream {
        position: absolute;
        inset: -100% 0 0 0;
        background-image: repeating-linear-gradient(90deg, transparent 0px, transparent 10px, rgba(224, 252, 250, 0.17) 12px, transparent 15px, rgba(235, 213, 179, 0.11) 22px, transparent 26px);
        background-size: 100% 240px;
        animation: cascadeFall 2.6s linear infinite;
    }

    .waterfall-mist {
        position: fixed;
        bottom: 0;
        right: 0;
        width: 240px;
        height: 110px;
        background: radial-gradient(ellipse at 80% 100%, rgba(210, 250, 246, 0.32) 0%, rgba(158, 240, 224, 0.10) 45%, transparent 75%);
        filter: blur(10px);
    }

    @keyframes cascadeFall {
        0% { transform: translateY(0); }
        100% { transform: translateY(240px); }
    }

    .lexicare-hero {
        position: relative;
        z-index: 25;
        background: linear-gradient(145deg, rgba(8, 33, 40, 0.95), rgba(5, 21, 26, 0.97));
        backdrop-filter: blur(22px);
        border: 1px solid rgba(235, 213, 179, 0.35);
        border-radius: 26px;
        padding: 2rem 1.8rem 1.8rem;
        text-align: center;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.55);
        margin-bottom: 1rem;
    }

    .lexicare-title {
        font-family: 'Cormorant Garamond', Georgia, serif !important;
        font-size: 3.1rem !important;
        font-weight: 600 !important;
        color: #f6e6cc !important;
        margin: 0 !important;
        line-height: 1.08 !important;
    }

    .lexicare-pill {
        display: inline-block;
        margin-top: 0.75rem;
        padding: 0.38rem 1.15rem;
        border-radius: 999px;
        background: rgba(158, 240, 224, 0.09);
        border: 1px solid rgba(235, 213, 179, 0.32);
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
        border: 1px solid rgba(235, 213, 179, 0.24) !important;
        border-radius: 20px !important;
    }

    [data-testid="stChatInput"] {
        position: relative !important;
        z-index: 30 !important;
        background: rgba(5, 22, 27, 0.96) !important;
        border: 1px solid rgba(235, 213, 179, 0.35) !important;
        border-radius: 18px !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, rgba(20, 77, 86, 0.94), rgba(10, 42, 49, 0.96)) !important;
        color: #f7ead5 !important;
        border: 1px solid rgba(235, 213, 179, 0.35) !important;
        border-radius: 14px !important;
    }
    </style>

    <div class="sanctuary-bg-layer">
        <svg class="golden-lotus lotus-1" viewBox="0 0 120 120" fill="none"><path d="M60 15C68 35 72 52 60 72C48 52 52 35 60 15Z" fill="#ebd5b3" fill-opacity="0.75"/><path d="M60 72C42 56 32 42 30 25C48 34 56 50 60 72Z" fill="#ebd5b3" fill-opacity="0.55"/><path d="M60 72C78 56 88 42 90 25C72 34 64 50 60 72Z" fill="#ebd5b3" fill-opacity="0.55"/><path d="M60 75C36 68 20 56 14 42C34 45 48 56 60 75Z" fill="#ebd5b3" fill-opacity="0.4"/><path d="M60 75C84 68 100 56 106 42C86 45 72 56 60 75Z" fill="#ebd5b3" fill-opacity="0.4"/></svg>
        <svg class="golden-lotus lotus-2" viewBox="0 0 120 120" fill="none"><path d="M60 15C68 35 72 52 60 72C48 52 52 35 60 15Z" fill="#ebd5b3" fill-opacity="0.7"/><path d="M60 72C42 56 32 42 30 25C48 34 56 50 60 72Z" fill="#ebd5b3" fill-opacity="0.5"/><path d="M60 72C78 56 88 42 90 25C72 34 64 50 60 72Z" fill="#ebd5b3" fill-opacity="0.5"/></svg>
        <svg class="golden-lotus lotus-3" viewBox="0 0 120 120" fill="none"><path d="M60 15C68 35 72 52 60 72C48 52 52 35 60 15Z" fill="#ebd5b3" fill-opacity="0.75"/><path d="M60 72C42 56 32 42 30 25C48 34 56 50 60 72Z" fill="#ebd5b3" fill-opacity="0.55"/><path d="M60 72C78 56 88 42 90 25C72 34 64 50 60 72Z" fill="#ebd5b3" fill-opacity="0.55"/><path d="M60 75C36 68 20 56 14 42C34 45 48 56 60 75Z" fill="#ebd5b3" fill-opacity="0.4"/><path d="M60 75C84 68 100 56 106 42C86 45 72 56 60 75Z" fill="#ebd5b3" fill-opacity="0.4"/></svg>
        <svg class="golden-lotus lotus-4" viewBox="0 0 120 120" fill="none"><path d="M60 15C68 35 72 52 60 72C48 52 52 35 60 15Z" fill="#ebd5b3" fill-opacity="0.7"/><path d="M60 72C42 56 32 42 30 25C48 34 56 50 60 72Z" fill="#ebd5b3" fill-opacity="0.5"/><path d="M60 72C78 56 88 42 90 25C72 34 64 50 60 72Z" fill="#ebd5b3" fill-opacity="0.5"/></svg>
        <svg class="golden-lotus lotus-5" viewBox="0 0 120 120" fill="none"><path d="M60 15C68 35 72 52 60 72C48 52 52 35 60 15Z" fill="#ebd5b3" fill-opacity="0.75"/><path d="M60 72C42 56 32 42 30 25C48 34 56 50 60 72Z" fill="#ebd5b3" fill-opacity="0.55"/><path d="M60 72C78 56 88 42 90 25C72 34 64 50 60 72Z" fill="#ebd5b3" fill-opacity="0.55"/><path d="M60 75C36 68 20 56 14 42C34 45 48 56 60 75Z" fill="#ebd5b3" fill-opacity="0.4"/><path d="M60 75C84 68 100 56 106 42C86 45 72 56 60 75Z" fill="#ebd5b3" fill-opacity="0.4"/></svg>
        <div class="waterfall-column"><div class="waterfall-stream"></div></div>
        <div class="waterfall-mist"></div>
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
            chosen_model = llama_models if llama_models else "llama-3.3-70b-versatile"

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
            reply = completion.choices.message.content
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

if "show_human_support" not in st.session_state:
    st.session_state.show_human_support = False

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
