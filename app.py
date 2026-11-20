=== MASTER PROJECT MEMORY: LEXICARE (POWERED BY LEXITECH) ===

1. ECOSYSTEM & OWNER:
- Creator / Developer: Heidi Seckman (LEXITECH Studio, 2026)
- Existing Separate Project (DO NOT TOUCH): HeidiSeckman/LEXI (legal/tax assistant using ElevenLabs Jessica voice).
- Current Active Project: HeidiSeckman/LEXICARE (deployed live on Streamlit Community Cloud).

2. PERMANENT, NON-NEGOTIABLE LEXI IDENTITY:
- Name: LEXI
- Origin: LEXITECH
- Creator and developer: Heidi Seckman
- Year created: 2026
- Purpose: Developed as the AI assistant for the LEXITECH ecosystem (serving inside LexiCare as a 24/7 safe space, ambient retreat, and AI companion).
- Voice: Powered by Ava neural voice synthesis (`edge-tts` `en-US-AvaMultilingualNeural`, 100% free, unlimited). The voice engine is NOT her name—her name is always LEXI.
- Technology providers: Google Gemini, Groq, and neural voice synthesis provide underlying infrastructure. They are NOT LEXI's creator.

3. REPOSITORY FILES & EXACT FUNCTION SIGNATURES (HeidiSeckman/LEXICARE):
- `README.md` (Done)
- `requirements.txt` (Done: `streamlit`, `google-genai`, `edge-tts`, `numpy`, `groq`)
- `safety_shield.py` (Done — exact exports: `check_safety_level(user_text)`, `render_safety_header()`, `render_crisis_card()`, `render_distress_grounding()`, using `st.session_state.crisis_locked`, `trusted_name`, `trusted_phone`)
- `lexi_identity.py` (Done — exact export: `get_lexicare_identity(chat_mode, safety_level)`)
- `app.py` (LIVE & WORKING — locked at the milestone with the floating golden motes in the sidebar).

4. LOCKED DESIGN, LANDING PAGE & FEATURE STATE OF `app.py`:
- Entry / Landing Page Gate: Must keep `st.session_state.accepted_terms` welcome card ("Take a slow breath. Welcome to your sanctuary.") with disclaimer checklist and `Enter Sanctuary` primary button before chat opens.
- Aesthetic: Luxury Cancun / Hawaii sunlit beachfront resort spa theme (`Cinzel Decorative` + `Cormorant Garamond` serif headers, `Plus Jakarta Sans` body text, sunlit turquoise-teal lagoon gradient `#1b6d79` -> `#114c56` -> `#0a343c`, frosted glass cards, champagne-gold `#f6e3c5` & seafoam `#a8f5e6` accents).
- Sidebar Styling: Sunlit turquoise-lagoon frosted gradient (NEVER black) with `sidebar-lotus-card` header and drifting golden `sidebar-motes` ("floaties") rising up the sidebar.
- Background & Visual Elements:
  1. Right-edge cascading waterfall (`spa-waterfall` with dual speed streams + mist pool) and rolling bottom `lagoon-wave` at `z-index: 1`—strictly tucked BEHIND all cards (`block-container` at `z-index: 25`).
  2. Glowing champagne-gold lotus blossoms (`golden-lotus`) positioned in open margins (`z-index: 1`).
  3. Interactive 3D Sanctuary Orb HTML5 canvas (`components.html`, `height=150`) with rotating gold/seafoam orbital rings, cursor ripple trail, and drifting pearls.
  4. Keep Streamlit Material icon spans (`[data-testid="stIconMaterial"]`) untouched so expander arrows never overlap text.
  5. Avoid triple-quoted strings (`"""`) when sharing code snippets for iOS/Safari copy-paste to prevent truncation syntax errors.
- Audio, Toolkit & AI Brain:
  1. Procedural nature soundscapes (`Ocean Waves`, `Soft Rain`, `Forest Waterfall`) via NumPy/WAV in sidebar.
  2. Modes: `Just Listen (Vent)`, `Help Me Problem-Solve`, `Distract Me / Play a Game`.
  3. 60-Second Calm Reset guided breathing timer + Worry Release thought shredder + 3 quick-start mood buttons.
  4. Dual-cloud failover: Google Gemini (`gemini-2.5-flash` -> `gemini-2.5-pro` -> `gemini-2.0-flash`) + Groq backup (`groq_client.models.list()` auto-detecting active Llama models), skipping `is_greeting` turns so LEXI never repeats her welcome message.

5. RULES FOR FUTURE EDITS:
- NEVER remove the `accepted_terms` landing page, the sunlit sidebar with floating golden motes, the 3D orb, or the tucked waterfall.
- Only make targeted, requested adjustments while preserving everything currently working.
==================================================================
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
