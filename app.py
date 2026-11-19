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

    .stApp {
        background: radial-gradient(circle at 20% 10%, #12474f 0%, #08232a 50%, #041317 100%) !important;
        color: #f3f7f5 !important;
    }

    [data-testid="stAppViewContainer"], .main, .block-container {
        background: transparent !important;
        position: relative;
        z-index: 2;
    }

    p, label, li, .stMarkdown, input, textarea {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #eef5f2 !important;
    }

    h1, h2, h3 {
        font-family: 'Cormorant Garamond', Georgia, serif !important;
        color: #ffffff !important;
    }

    [data-testid="stHeader"] {
        background: rgba(4, 19, 23, 0.45) !important;
        backdrop-filter: blur(10px);
    }

    [data-testid="stSidebar"] {
        background: rgba(6, 25, 31, 0.92) !important;
        backdrop-filter: blur(18px);
        border-right: 1px solid rgba(226, 194, 144, 0.24);
    }

    .lexi-hero {
        background: linear-gradient(145deg, rgba(16, 54, 62, 0.82), rgba(7, 26, 33, 0.90));
        backdrop-filter: blur(18px);
        border: 1px solid rgba(226, 194, 144, 0.35);
        border-radius: 24px;
        padding: 1.6rem 1.8rem;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 18px 42px rgba(0, 0, 0, 0.4);
    }

    .lexi-hero h1 {
        margin: 0;
        font-size: 2.75rem !important;
        background: linear-gradient(90deg, #ffffff, #ebd5b3, #b4f0e4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .lexi-badge {
        display: inline-block;
        margin-top: 0.45rem;
        padding: 0.28rem 1rem;
        border-radius: 999px;
        background: rgba(226, 194, 144, 0.14);
        border: 1px solid rgba(226, 194, 144, 0.4);
        color: #f2dfc1 !important;
        font-size: 0.76rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    [data-testid="stChatMessage"] {
        background: rgba(11, 40, 48, 0.86) !important;
        backdrop-filter: blur(14px);
        border: 1px solid rgba(132, 212, 198, 0.26);
        border-radius: 18px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 8px 26px rgba(0, 0, 0, 0.28);
    }

    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stExpander"] {
        background: rgba(9, 32, 39, 0.88) !important;
        border: 1px solid rgba(226, 194, 144, 0.28) !important;
        border-radius: 16px !important;
    }

    .stButton > button {
        border-radius: 12px !important;
        border: 1px solid rgba(226, 194, 144, 0.38) !important;
        background: rgba(15, 52, 62, 0.88) !important;
        color: #f6f8f7 !important;
        transition: all 0.22s ease;
    }

    .stButton > button:hover {
        background: rgba(38, 114, 116, 0.95) !important;
        border-color: #ebd3aa !important;
        color: #ffffff !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2b8c82, #1b6362) !important;
        border: 1px solid #ebd3aa !important;
    }

    textarea, input, [data-testid="stChatInput"] textarea {
        background-color: rgba(6, 23, 29, 0.94) !important;
        color: #f5f9f7 !important;
        border: 1px solid rgba(226, 194, 144, 0.38) !important;
        border-radius: 14px !important;
    }

    .sanctuary-water {
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 1;
        overflow: hidden;
    }

    .waterfall-column {
        position: absolute;
        top: 0;
        right: 3%;
        width: 190px;
        height: 100vh;
        background: linear-gradient(
            180deg,
            rgba(180, 245, 238, 0.02) 0%,
            rgba(130, 232, 224, 0.16) 45%,
            rgba(195, 250, 244, 0.32) 100%
        );
        mask-image: linear-gradient(90deg, transparent 0%, black 22%, black 78%, transparent 100%);
        -webkit-mask-image: linear-gradient(90deg, transparent 0%, black 22%, black 78%, transparent 100%);
    }

    .waterfall-streams {
        position: absolute;
        inset: -100% 0 0 0;
        background-image:
            repeating-linear-gradient(
                90deg,
                transparent 0px,
                rgba(220, 252, 248, 0.24) 3px,
                transparent 7px,
                rgba(115, 218, 210, 0.18) 14px,
                transparent 22px
            ),
            radial-gradient(circle at 50% 30%, rgba(255, 255, 255, 0.25) 0%, transparent 60%);
        background-size: 100% 220px, 100% 340px;
        animation: cascadeFall 2.6s linear infinite;
    }

    .waterfall-mist-pool {
        position: absolute;
        bottom: -25px;
        right: -2%;
        width: 340px;
        height: 130px;
        border-radius: 50%;
        background: radial-gradient(
            ellipse at center,
            rgba(215, 252, 248, 0.42) 0%,
            rgba(82, 204, 196, 0.22) 48%,
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
        height: 155px;
        animation: waveRoll 14s linear infinite;
    }

    @keyframes cascadeFall {
        0% { transform: translateY(0%); }
        100% { transform: translateY(50%); }
    }

    @keyframes mistPulse {
        0%, 100% { transform: scale(1) translateY(0px); opacity: 0.75; }
        50% { transform: scale(1.14) translateY(-8px); opacity: 1; }
    }

    @keyframes waveRoll {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }
    </style>

    <div class="sanctuary-water">
        <div class="waterfall-column">
            <div class="waterfall-streams"></div>
        </div>
        <div class="waterfall-mist-pool"></div>
        <svg class="lagoon-wave" viewBox="0 0 1440 160" preserveAspectRatio="none">
            <path d="M0,75 C360,145 720,5 1080,85 C1260,120 1350,95 1440,75 L1440,160 L0,160 Z" fill="rgba(45, 175, 168, 0.24)"></path>
        </svg>
    </div>
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
        <div class="lexi-badge">Powered by LexiTech • Private Sanctuary &amp; AI Companion</div>
    </div>
    """,
    unsafe_allow_html=True,
)

components.html(
    """
    <div style="width:100%; height:140px; border-radius:20px; overflow:hidden; position:relative;
                background: radial-gradient(circle at 50% 50%, rgba(36, 128, 126, 0.28), rgba(6, 22, 28, 0.85));
                border: 1px solid rgba(226, 194, 144, 0.28); box-shadow: inset 0 0 30px rgba(0,0,0,0.45);">
        <canvas id="orbCanvas" style="width:100%; height:100%; display:block; cursor:grab;"></canvas>
        <div style="position:absolute; bottom:10px; right:14px; font-family:sans-serif;
                    font-size:11px; letter-spacing:0.1em; text-transform:uppercase; color:rgba(240,222,192,0.75); pointer-events:none;">
            Move cursor to guide the sanctuary orb
        </div>
    </div>
    <script>
    const canvas = document.getElementById('orbCanvas');
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
                    reply_text = completion.choices[0].message.content
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
