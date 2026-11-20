import asyncio
import io
import os
import time
import wave
import edge_tts
from google import genai
from google.genai import types
from groq import Groq
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

LOTUS = "\U0001fab7"
HIBISCUS = "\U0001f33a"
SPARKLE = "\u2728"

st.set_page_config(
    page_title="LexiCare | Powered by LexiTech",
    page_icon=LOTUS,
    layout="centered",
    initial_sidebar_state="expanded",
)

if "accepted_terms" not in st.session_state:
    st.session_state.accepted_terms = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = True
if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "Just Listen (Vent)"
if "latest_voice_bytes" not in st.session_state:
    st.session_state.latest_voice_bytes = None

PAGE_STYLE = (
    '<link rel="preconnect" href="https://googleapis.com">'
    '<link rel="preconnect" href="https://gstatic.com" crossorigin>'
    '<link href="https://googleapis.com/css2?family=Cinzel+Decorative:wght@600;700&family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">'
    '<style>'
    ':root {'
    '  --glass-card: rgba(12, 56, 65, 0.90);'
    '  --gold-champagne: #f6e3c5;'
    '  --seafoam: #a8f5e6;'
    '  --text-main: #fbfefd;'
    '}'
    'html, body, .stApp,'
    '[data-testid="stAppViewContainer"],'
    '[data-testid="stMain"],'
    '[data-testid="stBottom"],'
    '[data-testid="stBottom"] > div,'
    '[data-testid="stBottomBlockContainer"] {'
    '  background: transparent !important;'
    '  color: var(--text-main) !important;'
    '  font-family: "Plus Jakarta Sans", -apple-system, BlinkMacSystemFont, sans-serif !important;'
    '}'
    '.stApp {'
    '  background: linear-gradient(145deg, #1b6d79 0%, #114c56 48%, #0a343c 100%) !important;'
    '  overflow-x: hidden !important;'
    '}'
    '[data-testid="stIconMaterial"], .material-symbols-rounded {'
    '  font-family: "Material Symbols Rounded" !important;'
    '  font-weight: normal !important;'
    '  font-style: normal !important;'
    '  letter-spacing: normal !important;'
    '  text-transform: none !important;'
    '  display: inline-block !important;'
    '  white-space: nowrap !important;'
    '  direction: ltr !important;'
    '}'
    '[data-testid="stHeader"] {'
    '  background: transparent !important;'
    '  z-index: 30 !important;'
    '}'
    '[data-testid="stSidebar"],'
    '[data-testid="stSidebar"] > div:first-child {'
    '  background:'
    '    radial-gradient(circle at 85% 12%, rgba(246, 227, 197, 0.18) 0%, transparent 45%),'
    '    radial-gradient(circle at 15% 88%, rgba(168, 245, 230, 0.16) 0%, transparent 50%),'
    '    linear-gradient(180deg, rgba(24, 96, 106, 0.94) 0%, rgba(14, 62, 70, 0.97) 100%) !important;'
    '  backdrop-filter: blur(22px) !important;'
    '  border-right: 1px solid rgba(246, 227, 197, 0.35) !important;'
    '  box-shadow: 6px 0 28px rgba(6, 30, 35, 0.28) !important;'
    '  z-index: 30 !important;'
    '}'
    '[data-testid="stSidebar"] label,'
    '[data-testid="stSidebar"] p,'
    '[data-testid="stSidebar"] span {'
    '  color: #f9fdfd !important;'
    '}'
    '.main .block-container,'
    '[data-testid="stAppViewBlockContainer"] {'
    '  position: relative !important;'
    '  z-index: 25 !important;'
    '}'
    'h1, h2, h3, .spa-serif {'
    '  font-family: "Cormorant Garamond", Georgia, serif !important;'
    '  letter-spacing: 0.02em !important;'
    '  color: var(--gold-champagne) !important;'
    '}'
    '.spa-waterfall {'
    '  position: fixed; top: 0; right: 0; width: 185px; height: 100vh;'
    '  z-index: 1; pointer-events: none;'
    '  background: linear-gradient(90deg, rgba(168, 245, 230, 0) 0%, rgba(168, 245, 230, 0.16) 28%, rgba(230, 255, 252, 0.32) 70%, rgba(246, 227, 197, 0.24) 100%);'
    '  overflow: hidden;'
    '}'
    '.spa-wf-stream1 {'
    '  position: absolute; top: -240px; left: 0; width: 100%; height: calc(100% + 240px);'
    '  background-image: repeating-linear-gradient(90deg, transparent 0px, transparent 8px, rgba(235, 255, 253, 0.30) 11px, transparent 14px, rgba(246, 227, 197, 0.22) 20px, transparent 25px);'
    '  background-size: 100% 240px;'
    '  animation: fallSlow 2.2s linear infinite;'
    '}'
    '.spa-wf-stream2 {'
    '  position: absolute; top: -180px; left: 0; width: 100%; height: calc(100% + 180px);'
    '  background-image: repeating-linear-gradient(90deg, transparent 0px, rgba(255, 255, 255, 0.45) 2px, transparent 5px, transparent 15px);'
    '  background-size: 100% 180px;'
    '  animation: fallFast 1.2s linear infinite;'
    '}'
    '@keyframes fallSlow { 0% { transform: translateY(0); } 100% { transform: translateY(240px); } }'
    '@keyframes fallFast { 0% { transform: translateY(0); } 100% { transform: translateY(180px); } }'
)
PAGE_STYLE_2 = (
    '<style>'
    '.spa-mist {'
    '  position: fixed; bottom: 0; right: 0; width: 310px; height: 130px; z-index: 1; pointer-events: none;'
    '  background: radial-gradient(ellipse at 82% 100%, rgba(235, 255, 252, 0.50) 0%, rgba(168, 245, 230, 0.18) 52%, transparent 78%);'
    '  filter: blur(10px);'
    '}'
    '.lagoon-wave {'
    '  position: fixed; bottom: -8px; left: 0; width: 200%; height: 145px; z-index: 1; pointer-events: none;'
    '  animation: waveRoll 14s linear infinite;'
    '}'
    '@keyframes waveRoll { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }'
    '.golden-lotus {'
    '  position: fixed; z-index: 1; pointer-events: none; opacity: 0.58;'
    '  filter: drop-shadow(0 0 14px rgba(252, 224, 158, 0.95)) drop-shadow(0 0 32px rgba(242, 196, 108, 0.75));'
    '  animation: lotusDrift 13s ease-in-out infinite;'
    '}'
    '.lotus-1 { top: 8%; left: 22rem; width: 105px; animation-delay: 0s; }'
    '.lotus-2 { top: 38%; left: 21.5rem; width: 88px; animation-delay: -3s; }'
    '.lotus-3 { bottom: 14%; left: 22.5rem; width: 112px; animation-delay: -6s; }'
    '.lotus-4 { top: 10%; right: 13%; width: 105px; animation-delay: -2s; }'
    '.lotus-5 { top: 42%; right: 14.5%; width: 92px; animation-delay: -5s; }'
    '.lotus-6 { bottom: 15%; right: 13.5%; width: 110px; animation-delay: -8s; }'
    '@keyframes lotusDrift { 0%, 100% { transform: translateY(0px) rotate(-3deg) scale(1); } 50% { transform: translateY(-16px) rotate(5deg) scale(1.05); } }'
    '.lexicare-hero {'
    '  position: relative; z-index: 25;'
    '  background: linear-gradient(145deg, rgba(16, 68, 78, 0.94), rgba(10, 46, 54, 0.96));'
    '  backdrop-filter: blur(22px);'
    '  border: 1px solid rgba(246, 227, 197, 0.48);'
    '  border-radius: 26px;'
    '  padding: 2rem 1.8rem 1.8rem;'
    '  text-align: center;'
    '  box-shadow: 0 18px 44px rgba(4, 24, 30, 0.42), inset 0 1px 0 rgba(255, 248, 235, 0.28);'
    '  margin-bottom: 1rem;'
    '}'
    '.lexicare-title {'
    '  font-family: "Cinzel Decorative", "Cormorant Garamond", Georgia, serif !important;'
    '  font-size: 2.95rem !important; font-weight: 700 !important; letter-spacing: 0.05em !important;'
    '  background: linear-gradient(90deg, #ffffff 0%, #f6e3c5 50%, #a8f5e6 100%);'
    '  -webkit-background-clip: text; -webkit-text-fill-color: transparent;'
    '  margin: 0 !important; line-height: 1.15 !important;'
    '}'
    '.lexicare-pill {'
    '  display: inline-block; margin-top: 0.75rem; padding: 0.4rem 1.25rem; border-radius: 999px;'
    '  background: rgba(168, 245, 230, 0.14); border: 1px solid rgba(246, 227, 197, 0.42);'
    '  color: var(--gold-champagne); font-size: 0.72rem; font-weight: 600;'
    '  letter-spacing: 0.15em; text-transform: uppercase;'
    '}'
    '[data-testid="stChatMessage"],'
    '[data-testid="stVerticalBlockBorderWrapper"],'
    '[data-testid="stExpander"] {'
    '  position: relative !important; z-index: 25 !important;'
    '  background: var(--glass-card) !important; backdrop-filter: blur(20px) !important;'
    '  border: 1px solid rgba(246, 227, 197, 0.34) !important;'
    '  border-radius: 20px !important;'
    '  box-shadow: 0 10px 28px rgba(4, 24, 30, 0.32) !important;'
    '}'
    '[data-testid="stChatInput"] {'
    '  position: relative !important; z-index: 30 !important;'
    '  background: rgba(12, 56, 65, 0.96) !important;'
    '  border: 1px solid rgba(246, 227, 197, 0.42) !important;'
    '  border-radius: 18px !important;'
    '}'
    '.stButton > button {'
    '  background: linear-gradient(135deg, rgba(28, 102, 112, 0.94), rgba(16, 68, 78, 0.96)) !important;'
    '  color: #fbf0dc !important; border: 1px solid rgba(246, 227, 197, 0.42) !important;'
    '  border-radius: 14px !important; transition: all 0.22s ease;'
    '}'
    '.stButton > button:hover {'
    '  border-color: #a8f5e6 !important;'
    '  box-shadow: 0 0 18px rgba(168, 245, 230, 0.32) !important;'
    '}'
    '.stButton > button[kind="primary"] {'
    '  background: linear-gradient(135deg, #2d958a, #1b6867) !important;'
    '  border: 1px solid #f6e3c5 !important; font-weight: 600 !important;'
    '}'
    '.sidebar-motes {'
    '  position: fixed; top: 0; left: 0; width: 21rem; height: 100vh;'
    '  pointer-events: none; z-index: 31; overflow: hidden;'
    '}'
    '.sidebar-mote {'
    '  position: absolute; bottom: -10px; border-radius: 50%;'
    '  background: radial-gradient(circle, #fffdf7 0%, #fbe4b4 55%, transparent 100%);'
    '  box-shadow: 0 0 8px rgba(251, 228, 180, 0.85);'
    '  animation: sidebarMoteRise linear infinite;'
    '}'
    '@keyframes sidebarMoteRise {'
    '  0% { transform: translateY(0px) translateX(0px); opacity: 0; }'
    '  15% { opacity: 0.85; }'
    '  85% { opacity: 0.75; }'
    '  100% { transform: translateY(-102vh) translateX(14px); opacity: 0; }'
    '}'
    '.sidebar-lotus-card {'
    '  background: linear-gradient(145deg, rgba(246, 227, 197, 0.16), rgba(168, 245, 230, 0.10));'
    '  border: 1px solid rgba(246, 227, 197, 0.42); border-radius: 18px;'
    '  padding: 1rem 0.9rem; text-align: center; margin-bottom: 1rem;'
    '  box-shadow: 0 8px 24px rgba(4, 24, 30, 0.25);'
    '}'
    '</style>'
    '<svg class="golden-lotus lotus-1" viewBox="0 0 120 120" fill="none"><path d="M60 12C69 34 73 52 60 74C47 52 51 34 60 12Z" fill="#fbe4b4" fill-opacity="0.95"/><path d="M60 74C40 57 30 42 28 24C47 34 55 51 60 74Z" fill="#f5e2c4" fill-opacity="0.80"/><path d="M60 74C80 57 90 42 92 24C73 34 65 51 60 74Z" fill="#f5e2c4" fill-opacity="0.80"/><path d="M60 77C34 70 18 57 12 42C33 45 47 57 60 77Z" fill="#f5e2c4" fill-opacity="0.65"/><path d="M60 77C86 70 102 57 108 42C87 45 73 57 60 77Z" fill="#f5e2c4" fill-opacity="0.65"/></svg>'
    '<svg class="golden-lotus lotus-2" viewBox="0 0 120 120" fill="none"><path d="M60 12C69 34 73 52 60 74C47 52 51 34 60 12Z" fill="#fbe4b4" fill-opacity="0.92"/><path d="M60 74C40 57 30 42 28 24C47 34 55 51 60 74Z" fill="#f5e2c4" fill-opacity="0.78"/><path d="M60 74C80 57 90 42 92 24C73 34 65 51 60 74Z" fill="#f5e2c4" fill-opacity="0.78"/></svg>'
    '<svg class="golden-lotus lotus-3" viewBox="0 0 120 120" fill="none"><path d="M60 12C69 34 73 52 60 74C47 52 51 34 60 12Z" fill="#fbe4b4" fill-opacity="0.95"/><path d="M60 74C40 57 30 42 28 24C47 34 55 51 60 74Z" fill="#f5e2c4" fill-opacity="0.80"/><path d="M60 74C80 57 90 42 92 24C73 34 65 51 60 74Z" fill="#f5e2c4" fill-opacity="0.80"/><path d="M60 77C34 70 18 57 12 42C33 45 47 57 60 77Z" fill="#f5e2c4" fill-opacity="0.65"/><path d="M60 77C86 70 102 57 108 42C87 45 73 57 60 77Z" fill="#f5e2c4" fill-opacity="0.65"/></svg>'
    '<svg class="golden-lotus lotus-4" viewBox="0 0 120 120" fill="none"><path d="M60 12C69 34 73 52 60 74C47 52 51 34 60 12Z" fill="#fbe4b4" fill-opacity="0.92"/><path d="M60 74C40 57 30 42 28 24C47 34 55 51 60 74Z" fill="#f5e2c4" fill-opacity="0.78"/><path d="M60 74C80 57 90 42 92 24C73 34 65 51 60 74Z" fill="#f5e2c4" fill-opacity="0.78"/></svg>'
    '<svg class="golden-lotus lotus-5" viewBox="0 0 120 120" fill="none"><path d="M60 12C69 34 73 52 60 74C47 52 51 34 60 12Z" fill="#fbe4b4" fill-opacity="0.95"/><path d="M60 74C40 57 30 42 28 24C47 34 55 51 60 74Z" fill="#f5e2c4" fill-opacity="0.80"/><path d="M60 74C80 57 90 42 92 24C73 34 65 51 60 74Z" fill="#f5e2c4" fill-opacity="0.80"/></svg>'
    '<svg class="golden-lotus lotus-6" viewBox="0 0 120 120" fill="none"><path d="M60 12C69 34 73 52 60 74C47 52 51 34 60 12Z" fill="#fbe4b4" fill-opacity="0.92"/><path d="M60 74C40 57 30 42 28 24C47 34 55 51 60 74Z" fill="#f5e2c4" fill-opacity="0.78"/><path d="M60 74C80 57 90 42 92 24C73 34 65 51 60 74Z" fill="#f5e2c4" fill-opacity="0.78"/></svg>'
    '<div class="spa-waterfall"><div class="spa-wf-stream1"></div><div class="spa-wf-stream2"></div></div>'
    '<div class="spa-mist"></div>'
    '<svg class="lagoon-wave" viewBox="0 0 1440 160" preserveAspectRatio="none">'
    '<path d="M0,75 C360,145 720,5 1080,85 C1260,120 1350,95 1440,75 L1440,160 L0,160 Z" fill="rgba(45, 175, 168, 0.24)"></path>'
    '</svg>'
)
st.markdown(PAGE_STYLE + PAGE_STYLE_2, unsafe_allow_html=True)
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
    f'<div class="lexicare-hero">'
    f'<h1 class="lexicare-title">{LOTUS} LexiCare</h1>'
    f'<div class="lexicare-pill">Powered by LexiTech &bull; Private Sanctuary &amp; AI Companion</div>'
    f'</div>',
    unsafe_allow_html=True,
)

ORB_HTML = (
    '<style>html, body { margin: 0; padding: 0; background: transparent; overflow: hidden; }</style>'
    '<div style="box-sizing:border-box; position:relative; width:100%; height:148px; border-radius:22px; overflow:hidden;'
    ' background: radial-gradient(circle at 30% 40%, rgba(25,104,115,0.92), rgba(10,48,56,0.96));'
    ' border: 1px solid rgba(246, 227, 197, 0.38);">'
    '<canvas id="orbCanvas" style="width:100%; height:100%; display:block; cursor:crosshair;"></canvas>'
    '<div style="position:absolute; bottom:10px; right:16px; font-family:\'Plus Jakarta Sans\',sans-serif;'
    ' font-size:11px; letter-spacing:0.12em; color:#f6e3c5; opacity:0.88; pointer-events:none;">'
    'MOVE CURSOR TO GUIDE THE SANCTUARY ORB</div>'
    '</div>'
    '<script>'
    'const canvas = document.getElementById("orbCanvas");'
    'const ctx = canvas.getContext("2d");'
    'function resize() {'
    '  canvas.width = canvas.offsetWidth * window.devicePixelRatio;'
    '  canvas.height = canvas.offsetHeight * window.devicePixelRatio;'
    '  ctx.scale(window.devicePixelRatio, window.devicePixelRatio);'
    '}'
    'resize();'
    'window.addEventListener("resize", resize);'
    'let targetX = canvas.offsetWidth * 0.28;'
    'let targetY = canvas.offsetHeight * 0.50;'
    'let orbX = targetX; let orbY = targetY; let angle = 0;'
    'const pearls = Array.from({ length: 22 }, (_, i) => ({'
    '  x: Math.random() * 650, y: Math.random() * 148,'
    '  r: 1.4 + Math.random() * 2.8, speed: 0.25 + Math.random() * 0.55, gold: i % 2 === 0'
    '}));'
    'const trail = [];'
    'canvas.addEventListener("mousemove", (e) => {'
    '  const rect = canvas.getBoundingClientRect();'
    '  targetX = e.clientX - rect.left; targetY = e.clientY - rect.top;'
    '  trail.push({ x: targetX, y: targetY, alpha: 0.55, r: 8 });'
    '  if (trail.length > 18) trail.shift();'
    '});'
    'function animate() {'
    '  const w = canvas.offsetWidth; const h = canvas.offsetHeight;'
    '  ctx.clearRect(0, 0, w, h);'
    '  angle += 0.025;'
    '  orbX += (targetX - orbX) * 0.08; orbY += (targetY - orbY) * 0.08;'
    '  pearls.forEach(p => {'
    '    p.y -= p.speed;'
    '    if (p.y < -5) { p.y = h + 5; p.x = Math.random() * w; }'
    '    ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);'
    '    ctx.fillStyle = p.gold ? "rgba(251, 228, 180, 0.65)" : "rgba(168, 245, 230, 0.55)";'
    '    ctx.fill();'
    '  });'
    '  trail.forEach(t => {'
    '    t.alpha *= 0.92; t.r += 0.35;'
    '    ctx.beginPath(); ctx.arc(t.x, t.y, t.r, 0, Math.PI * 2);'
    '    ctx.strokeStyle = `rgba(245, 226, 196, ${t.alpha})`;'
    '    ctx.lineWidth = 1.2; ctx.stroke();'
    '  });'
    '  const pulse = Math.sin(angle * 1.4) * 5;'
    '  const outerGlow = ctx.createRadialGradient(orbX, orbY, 4, orbX, orbY, 64 + pulse);'
    '  outerGlow.addColorStop(0, "rgba(255, 253, 248, 0.98)");'
    '  outerGlow.addColorStop(0.25, "rgba(251, 228, 180, 0.65)");'
    '  outerGlow.addColorStop(0.58, "rgba(168, 245, 230, 0.28)");'
    '  outerGlow.addColorStop(1, "rgba(168, 245, 230, 0)");'
    '  ctx.beginPath(); ctx.arc(orbX, orbY, 64 + pulse, 0, Math.PI * 2);'
    '  ctx.fillStyle = outerGlow; ctx.fill();'
    '  ctx.save(); ctx.translate(orbX, orbY); ctx.rotate(angle);'
    '  ctx.beginPath(); ctx.ellipse(0, 0, 34, 13, 0, 0, Math.PI * 2);'
    '  ctx.strokeStyle = "rgba(251, 228, 180, 0.65)"; ctx.lineWidth = 1.4; ctx.stroke();'
    '  ctx.rotate(-angle * 1.8);'
    '  ctx.beginPath(); ctx.ellipse(0, 0, 28, 11, Math.PI / 3, 0, Math.PI * 2);'
    '  ctx.strokeStyle = "rgba(168, 245, 230, 0.60)"; ctx.lineWidth = 1.2; ctx.stroke();'
    '  ctx.restore();'
    '  const sphereGrad = ctx.createRadialGradient(orbX - 5, orbY - 5, 2, orbX, orbY, 18);'
    '  sphereGrad.addColorStop(0, "#ffffff");'
    '  sphereGrad.addColorStop(0.55, "#fbe4b4");'
    '  sphereGrad.addColorStop(1, "rgba(168, 245, 230, 0.85)");'
    '  ctx.beginPath(); ctx.arc(orbX, orbY, 18, 0, Math.PI * 2);'
    '  ctx.fillStyle = sphereGrad; ctx.fill();'
    '  requestAnimationFrame(animate);'
    '}'
    'animate();'
    '</script>'
)
components.html(ORB_HTML, height=150)

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
async def _synthesize_ava_async(text: str, rate: str, pitch: str) -> bytes:
    communicate = edge_tts.Communicate(
        text,
        "en-US-AvaMultilingualNeural",
        rate=rate,
        pitch=pitch,
    )
    chunks = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.extend(chunk["data"])
    return bytes(chunks)


def speak_text(text: str, mode: str, safety_level: str):
    clean = text.replace("*", "").replace("#", "").strip()
    if not clean:
        return
    if safety_level == "DISTRESS":
        rate, pitch = "-10%", "-2Hz"
    elif mode == "Just Listen (Vent)":
        rate, pitch = "-6%", "-1Hz"
    elif mode == "Distract Me / Play a Game":
        rate, pitch = "+2%", "+1Hz"
    else:
        rate, pitch = "-3%", "+0Hz"
    try:
        audio_bytes = asyncio.run(_synthesize_ava_async(clean, rate, pitch))
        if audio_bytes:
            st.session_state.latest_voice_bytes = audio_bytes
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)
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

    gemini_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", "")).strip()
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

    groq_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", "")).strip()
    if groq_key:
        try:
            groq_client = Groq(api_key=groq_key)
            available = [
                m.id
                for m in groq_client.models.list().data
                if "whisper" not in m.id.lower()
                and "guard" not in m.id.lower()
                and "tts" not in m.id.lower()
                and "gpt" not in m.id.lower()
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
    st.markdown(
        '<div class="sidebar-motes">'
        '<span class="sidebar-mote" style="left:12%; width:3px; height:3px; animation-duration:11s; animation-delay:0s;"></span>'
        '<span class="sidebar-mote" style="left:28%; width:4px; height:4px; animation-duration:14s; animation-delay:-3s;"></span>'
        '<span class="sidebar-mote" style="left:45%; width:2.5px; height:2.5px; animation-duration:9.5s; animation-delay:-6s;"></span>'
        '<span class="sidebar-mote" style="left:62%; width:4.5px; height:4.5px; animation-duration:15s; animation-delay:-2s;"></span>'
        '<span class="sidebar-mote" style="left:78%; width:3px; height:3px; animation-duration:12s; animation-delay:-8s;"></span>'
        '<span class="sidebar-mote" style="left:18%; width:3.5px; height:3.5px; animation-duration:13s; animation-delay:-5s;"></span>'
        '<span class="sidebar-mote" style="left:52%; width:3px; height:3px; animation-duration:10.5s; animation-delay:-9s;"></span>'
        '<span class="sidebar-mote" style="left:85%; width:4px; height:4px; animation-duration:16s; animation-delay:-4s;"></span>'
        '<span class="sidebar-mote" style="left:36%; width:2.5px; height:2.5px; animation-duration:11.5s; animation-delay:-7s;"></span>'
        '<span class="sidebar-mote" style="left:70%; width:3.5px; height:3.5px; animation-duration:13.5s; animation-delay:-1s;"></span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="sidebar-lotus-card">'
        f'<div style="font-size:1.85rem; margin-bottom:0.2rem;">{LOTUS}</div>'
        f'<div style="font-family:\'Cinzel Decorative\',\'Cormorant Garamond\',serif; font-size:1.25rem; font-weight:700; color:#fbf0dc;">'
        f'Sanctuary Controls</div>'
        f'<div style="font-size:0.70rem; letter-spacing:0.14em; text-transform:uppercase; color:#a8f5e6; margin-top:0.25rem;">'
        f'Twilight Lagoon Retreat</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.header(f"{LOTUS} Spa Soundscapes")
    ambient_choice = st.selectbox(
        "Ambient Sanctuary Audio",
        ["Off", "Ocean Waves", "Soft Rain", "Forest Waterfall"],
    )
    if ambient_choice != "Off":
        sound_bytes = generate_nature_sound(ambient_choice)
        st.audio(sound_bytes, format="audio/wav", loop=True, autoplay=True)
        st.caption(f"Streaming {ambient_choice.lower()} in the background.")

    st.divider()
    st.header(f"{HIBISCUS} Sanctuary Mode")
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
    st.subheader(f"{LOTUS} 60-Second Calm Reset")
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
    st.subheader(f"{LOTUS} Worry Release")
    worry = st.text_area(
        "Write a thought you want to let go of:",
        placeholder="Type it here, then release it into the tide...",
        height=80,
    )
    if st.button("Release Thought", use_container_width=True):
        if worry.strip():
            st.toast(f"Released and washed away. {LOTUS}")
            st.rerun()

    st.divider()
    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.latest_voice_bytes = None
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
    avatar = LOTUS if msg["role"] == "assistant" else SPARKLE
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])

st.caption("Need a starting point? Tap one:")
q1, q2, q3 = st.columns(3)
quick_prompt = None
if q1.button("I'm feeling overwhelmed", use_container_width=True):
    quick_prompt = "I'm feeling really overwhelmed right now and just need someone to talk to."
if q2.button("Can't sleep / lonely", use_container_width=True):
    quick_prompt = "I'm up late feeling lonely and my brain won't turn off."
if q3.button("Play a calming game", use_container_width=True):
    quick_prompt = "Can we play a fun, low-stress mini-game right here in chat to distract me?"

user_input = st.chat_input("Speak with Lexi...")
prompt = quick_prompt or user_input

if prompt:
    safety_level = check_safety_level(prompt)
    if safety_level == "CRISIS":
        st.session_state.crisis_locked = True
        st.rerun()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=SPARKLE):
        st.write(prompt)

    if safety_level == "DISTRESS":
        render_distress_grounding()

    system_prompt = get_lexicare_identity(st.session_state.chat_mode, safety_level)

    with st.chat_message("assistant", avatar=LOTUS):
        with st.spinner("Lexi is listening..."):
            reply = generate_lexi_reply(system_prompt, st.session_state.messages)
        st.write(reply)
        if st.session_state.voice_enabled:
            speak_text(reply, st.session_state.chat_mode, safety_level)

    st.session_state.messages.append({"role": "assistant", "content": reply})
