import re
import urllib.parse
import streamlit as st

CRISIS_PATTERNS = [
    r"\b(kill|hurt|harm|end)\s+(myself|my\s*self|my\s*life)\b",
    r"\b(suicid(e|al)|unalive\s*(myself|me)?|want\s*to\s*die|better\s*off\s*dead)\b",
    r"\b(overdose|cut\s*myself|self[\s-]*harm|no\s*reason\s*to\s*live)\b",
]

DISTRESS_PATTERNS = [
    r"\b(panic\s*attack|can'?t\s*breathe|freaking\s*out|falling\s*apart)\b",
    r"\b(hopeless|worthless|nobody\s*cares|completely\s*alone)\b",
]


def check_safety_level(user_text: str) -> str:
    """Returns 'CRISIS', 'DISTRESS', or 'SAFE'."""
    cleaned = user_text.lower().strip()
    for pattern in CRISIS_PATTERNS:
        if re.search(pattern, cleaned):
            return "CRISIS"
    for pattern in DISTRESS_PATTERNS:
        if re.search(pattern, cleaned):
            return "DISTRESS"
    return "SAFE"


def render_safety_header():
    """Always-visible top bar with Trusted Contact setup and instant help button."""
    if "crisis_locked" not in st.session_state:
        st.session_state.crisis_locked = False
    if "trusted_name" not in st.session_state:
        st.session_state.trusted_name = ""
    if "trusted_phone" not in st.session_state:
        st.session_state.trusted_phone = ""

    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(
            "Lexi is an AI companion for reflection and calm—not a therapist or medical professional."
        )
    with col2:
        if st.button("🆘 Human Support", use_container_width=True):
            st.session_state.crisis_locked = True
            st.rerun()

    with st.expander("💛 Optional: Set a Trusted Person (Quick-Alert Contact)"):
        t_name = st.text_input(
            "Trusted Person's Name",
            value=st.session_state.trusted_name,
            placeholder="e.g., Mom, Sarah, Alex",
        )
        t_phone = st.text_input(
            "Their Mobile Number (for 1-tap text)",
            value=st.session_state.trusted_phone,
            placeholder="e.g., 5551234567",
        )
        if st.button("Save Trusted Contact"):
            st.session_state.trusted_name = t_name.strip()
            st.session_state.trusted_phone = re.sub(r"[^\d+]", "", t_phone)
            st.success("Saved for this session.")


def render_crisis_card():
    """Full-stop safety takeover card with 1-tap native mobile links."""
    st.error("### You don't have to carry this alone. Real people are here right now.")
    st.write(
        "Lexi has paused normal chat so you can connect directly with free, confidential human support."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.link_button("📞 Call 988 (Lifeline)", "tel:988", use_container_width=True)
    with c2:
        st.link_button(
            "💬 Text 988", "sms:988?&body=HELLO", use_container_width=True
        )
    with c3:
        st.link_button("🚨 Call 911", "tel:911", use_container_width=True)

    st.link_button(
        "📱 Text HOME to 741741 (Crisis Text Line)",
        "sms:741741?&body=HOME",
        use_container_width=True,
    )

    if st.session_state.trusted_phone:
        person = st.session_state.trusted_name or "my trusted contact"
        msg = urllib.parse.quote(
            "Hey, I'm having a really hard time right now and could really use someone to talk to."
        )
        sms_uri = f"sms:{st.session_state.trusted_phone}?&body={msg}"
        st.link_button(
            f"💛 Text {person} Now",
            sms_uri,
            type="primary",
            use_container_width=True,
        )

    st.divider()
    if st.button("I am safe now — unlock chat"):
        st.session_state.crisis_locked = False
        st.rerun()


def render_distress_grounding():
    """Preventive de-escalation box for panic or heavy overwhelm."""
    with st.container(border=True):
        st.info("### Let's slow things down for 60 seconds.")
        st.markdown(
            "**Try the 5-4-3-2-1 Grounding Reset while you're here:**\n"
            "- **5** things you can see around you\n"
            "- **4** things you can physically touch\n"
            "- **3** things you can hear right now\n"
            "- **2** things you can smell\n"
            "- **1** slow breath in for 4 seconds, hold for 4, out for 6"
        )
