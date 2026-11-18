import asyncio
import os
import re
import tempfile
import edge_tts
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="VEXON Voice Studio",
    page_icon="🎙️",
    layout="centered",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None,
    },
)

# Custom CSS: Google Fonts, Sticky Branding, Unified Dark Theme & Bright Luminous Light Theme
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* Global Font Family */
    html, body, [class*="css"], .stApp, button, input, textarea, select {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Keep Streamlit top header transparent so 3-dot menu stays clickable */
    header[data-testid="stHeader"] {
        background: transparent !important;
        z-index: 100002 !important;
        pointer-events: none;
    }
    header[data-testid="stHeader"] * {
        pointer-events: auto;
    }

    /* Hide GitHub icon, Share, Star, and Deploy buttons */
    [data-testid="stToolbarActions"],
    .stDeployButton,
    a[href*="github.com"],
    button[title="View app source"] {
        display: none !important;
    }

    /* Hide Streamlit Footer */
    footer {
        visibility: hidden !important;
    }

    /* Sleek Fixed/Sticky Branding Bar at the top */
    .vexon-navbar {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 60px;
        background: linear-gradient(90deg, #13112b 0%, #2a0e3b 50%, #13112b 100%);
        border-bottom: 1.5px solid rgba(168, 85, 247, 0.5);
        display: flex;
        align-items: center;
        justify-content: flex-start;
        padding: 0 22px;
        z-index: 100000;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
    }

    .vexon-brand-box {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .vexon-title {
        font-size: 1.45rem;
        font-weight: 800;
        letter-spacing: 2.5px;
        background: linear-gradient(90deg, #e879f9, #a855f7, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1;
    }

    .vexon-badge {
        font-size: 0.68rem;
        color: #e9d5ff;
        background: rgba(168, 85, 247, 0.22);
        border: 1px solid rgba(168, 85, 247, 0.45);
        padding: 3px 9px;
        border-radius: 12px;
        letter-spacing: 0.9px;
        font-weight: 600;
    }

    /* Push main app content below fixed navbar */
    .block-container {
        padding-top: 84px !important;
        padding-bottom: 40px !important;
    }

    /* =========================================
       1. DARK THEME STYLING (Default)
       ========================================= */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #0b0d17 !important;
        color: #f8fafc !important;
    }

    .stApp h1, .stApp h2, .stApp h3 {
        color: #f8fafc !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px;
    }

    .stApp label, .stApp p, .stApp span {
        color: #e2e8f0;
    }

    /* Textarea, Search Input & Both Selectboxes in Dark Mode */
    .stApp .stTextArea textarea,
    .stApp .stTextInput input,
    .stApp [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background-color: #141829 !important;
        color: #f8fafc !important;
        border: 1px solid rgba(168, 85, 247, 0.35) !important;
        border-radius: 12px !important;
        transition: all 0.2s ease-in-out;
    }

    /* Inner text & placeholders of Selectboxes in Dark Mode */
    .stApp [data-testid="stSelectbox"] div[data-baseweb="select"] div,
    .stApp [data-testid="stSelectbox"] div[data-baseweb="select"] span {
        background-color: transparent !important;
        color: #f8fafc !important;
    }

    .stApp .stTextArea textarea::placeholder,
    .stApp .stTextInput input::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
    }

    .stApp .stTextArea textarea:focus,
    .stApp .stTextInput input:focus,
    .stApp [data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
        border-color: #a855f7 !important;
        box-shadow: 0 0 0 2px rgba(168, 85, 247, 0.25) !important;
    }

    /* Dropdown Menu Popup List in Dark Mode */
    div[data-baseweb="popover"] ul {
        background-color: #141829 !important;
        border: 1px solid rgba(168, 85, 247, 0.35) !important;
    }
    div[data-baseweb="popover"] li {
        color: #f8fafc !important;
    }
    div[data-baseweb="popover"] li:hover {
        background-color: rgba(168, 85, 247, 0.25) !important;
    }

    /* Advance Expander in Dark Mode */
    .stApp div[data-testid="stExpander"] {
        background-color: #141829 !important;
        border: 1px solid rgba(168, 85, 247, 0.3) !important;
        border-radius: 12px !important;
    }
    .stApp div[data-testid="stExpander"] summary,
    .stApp div[data-testid="stExpander"] summary p {
        color: #f8fafc !important;
    }

    /* =========================================
       2. BRIGHT LUMINOUS LIGHT THEME STYLING
       (Triggers automatically when Streamlit Theme = Light)
       ========================================= */
    @container style(--background-color: #ffffff) {
        .stApp, [data-testid="stAppViewContainer"] {
            background: linear-gradient(180deg, #f5f3ff 0%, #ffffff 45%, #f8fafc 100%) !important;
            color: #09090b !important;
        }

        .stApp h1, .stApp h2, .stApp h3 {
            color: #09090b !important;
            font-weight: 800 !important;
        }

        .stApp label, .stApp p, .stApp span {
            color: #111827 !important;
            font-weight: 500;
        }

        /* Crisp Bright White Inputs & Selectboxes with Royal Purple Accent */
        .stApp .stTextArea textarea,
        .stApp .stTextInput input,
        .stApp [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            color: #09090b !important;
            border: 1.5px solid rgba(124, 58, 237, 0.32) !important;
            box-shadow: 0 4px 14px rgba(124, 58, 237, 0.07) !important;
        }

        .stApp [data-testid="stSelectbox"] div[data-baseweb="select"] div,
        .stApp [data-testid="stSelectbox"] div[data-baseweb="select"] span {
            background-color: transparent !important;
            color: #09090b !important;
        }

        .stApp .stTextArea textarea::placeholder,
        .stApp .stTextInput input::placeholder {
            color: #6b7280 !important;
            opacity: 1 !important;
        }

        .stApp .stTextArea textarea:focus,
        .stApp .stTextInput input:focus,
        .stApp [data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
            border-color: #7c3aed !important;
            box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.18) !important;
        }

        /* Advance Expander in Bright Light Mode */
        .stApp div[data-testid="stExpander"] {
            background-color: #ffffff !important;
            border: 1.5px solid rgba(124, 58, 237, 0.28) !important;
            box-shadow: 0 4px 14px rgba(124, 58, 237, 0.06) !important;
        }
        .stApp div[data-testid="stExpander"] summary,
        .stApp div[data-testid="stExpander"] summary p {
            color: #09090b !important;
            font-weight: 600 !important;
        }
    }

    /* Primary Generate Button Styling (Matches VEXON Branding) */
    button[kind="primary"] {
        background: linear-gradient(135deg, #9333ea 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.65rem 1.2rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.4px;
        box-shadow: 0 6px 18px rgba(124, 58, 237, 0.35) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }

    button[kind="primary"] p, button[kind="primary"] span {
        color: #ffffff !important;
    }

    button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 24px rgba(124, 58, 237, 0.5) !important;
    }

    /* Download Buttons Styling */
    div[data-testid="stDownloadButton"] button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: 1.5px solid rgba(139, 92, 246, 0.45) !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stDownloadButton"] button:hover {
        border-color: #8b5cf6 !important;
        background-color: rgba(139, 92, 246, 0.12) !important;
    }

    /* Audio Player Rounded Styling */
    audio {
        width: 100%;
        border-radius: 12px;
        margin-top: 8px;
        margin-bottom: 12px;
    }
    </style>

    <div class="vexon-navbar">
        <div class="vexon-brand-box">
            <svg width="32" height="32" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="vexonGrad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
                        <stop offset="0%" stop-color="#e879f9"/>
                        <stop offset="50%" stop-color="#9333ea"/>
                        <stop offset="100%" stop-color="#3b82f6"/>
                    </linearGradient>
                </defs>
                <rect x="2" y="2" width="36" height="36" rx="10" fill="url(#vexonGrad)" fill-opacity="0.18" stroke="url(#vexonGrad)" stroke-width="2.2"/>
                <path d="M11 12L20 29L29 12" stroke="url(#vexonGrad)" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="20" cy="13" r="2.2" fill="#e879f9"/>
            </svg>
            <span class="vexon-title">VEXON</span>
            <span class="vexon-badge">VOICE STUDIO</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# Fetch all available voices dynamically
@st.cache_data
async def get_all_voices():
  voices = await edge_tts.list_voices()
  return voices


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
all_voices = loop.run_until_complete(get_all_voices())


# Clean text helper: removes Natural, Neural, Microsoft, Online, and all brackets
def clean_text(text):
  for word in ["Microsoft", "Online", "Natural", "Neural"]:
    text = re.sub(word, "", text, flags=re.IGNORECASE)
  text = re.sub(r"[(),\-]", " ", text)
  return " ".join(text.split()).strip()


# Group voices by clean Language & Country
def get_language_country_groups(voices):
  groups = {}
  for v in voices:
    friendly = v.get("FriendlyName", "")
    locale = v.get("Locale", "")

    if " - " in friendly:
      raw_lang = friendly.split(" - ")[-1]
    else:
      raw_lang = locale

    lang_country = clean_text(raw_lang)
    if not lang_country:
      lang_country = locale

    if lang_country not in groups:
      groups[lang_country] = []
    groups[lang_country].append(v)
  return groups


lang_groups = get_language_country_groups(all_voices)
sorted_languages = sorted(list(lang_groups.keys()))


# Async function for Edge TTS generation
async def generate_tts(
    text, voice_id, rate_val, pitch_val, generate_srt
):
  rate_str = "+0%" if rate_val == 0 else f"{rate_val:+d}%"
  pitch_str = "+0Hz" if pitch_val == 0 else f"{pitch_val:+d}Hz"

  temp_dir = tempfile.mkdtemp()
  audio_path = os.path.join(temp_dir, "vexon_output.mp3")
  srt_path = os.path.join(temp_dir, "vexon_subtitles.srt")
  txt_path = os.path.join(temp_dir, "vexon_script.txt")

  communicate = edge_tts.Communicate(
      text, voice_id, rate=rate_str, pitch=pitch_str
  )

  subtitles_content = []
  audio_data = bytearray()
  sub_index = 1

  async for chunk in communicate.stream():
    if chunk["type"] == "audio":
      audio_data.extend(chunk["data"])
    elif chunk["type"] == "WordBoundary" and generate_srt:
      start_time = chunk["offset"] / 10000000
      duration = chunk["duration"] / 10000000
      end_time = start_time + duration
      word = chunk["text"]

      def format_time(seconds):
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

      subtitles_content.append(
          f"{sub_index}\n{format_time(start_time)} -->"
          f" {format_time(end_time)}\n{word}\n"
      )
      sub_index += 1

  with open(audio_path, "wb") as f:
    f.write(audio_data)

  with open(txt_path, "w", encoding="utf-8") as f:
    f.write(text)

  final_srt_path = None
  if generate_srt and subtitles_content:
    with open(srt_path, "w", encoding="utf-8") as f:
      f.write("\n".join(subtitles_content))
    final_srt_path = srt_path

  return audio_path, final_srt_path, txt_path


# Empty Text Box at Start
text_input = st.text_area(
    "Enter Text for Speech",
    value="",
    placeholder="Type or paste your script here...",
    height=150,
)

st.markdown("### 🌐 Language & Voice Selection")

# Smart Search Bar
search_query = st.text_input(
    "🔍 Smart Search",
    value="",
    placeholder="e.g. English United States, Jenny",
)

query_tokens = clean_text(search_query).lower().split()

if query_tokens:
  matched_languages = []
  for lang in sorted_languages:
    voices_in_lang = lang_groups[lang]
    voice_names_str = " ".join([
        clean_text(v.get("ShortName", "").split("-")[-1])
        + " "
        + v.get("Gender", "")
        for v in voices_in_lang
    ])
    full_searchable_text = f"{lang} {voice_names_str}".lower()

    if all(token in full_searchable_text for token in query_tokens):
      matched_languages.append(lang)

  if not matched_languages:
    matched_languages = sorted_languages
    st.warning("No exact match found. Showing all languages.")
else:
  matched_languages = sorted_languages

# Tab 1: Language & Country Selector
selected_language = st.selectbox(
    "1️⃣ Select Language & Country",
    matched_languages,
    index=None,
    placeholder="Choose a language & country...",
)

# Tab 2: Voice Selector
voice_dict = {}
if selected_language:
  available_voices_in_lang = lang_groups.get(selected_language, [])
  for v in available_voices_in_lang:
    short_name = v.get("ShortName", "")
    parts = short_name.split("-")
    raw_voice = parts[-1] if len(parts) >= 3 else "Voice"
    voice_name = clean_text(raw_voice)
    gender = v.get("Gender", "Unknown")

    display_label = f"{voice_name} - {gender}"
    voice_dict[display_label] = v["ShortName"]

  if query_tokens:
    filtered_voice_dict = {
        label: vid
        for label, vid in voice_dict.items()
        if all(token in label.lower() for token in query_tokens)
    }
    if filtered_voice_dict:
      voice_dict = filtered_voice_dict

selected_voice_label = st.selectbox(
    "2️⃣ Select Voice & Gender",
    list(voice_dict.keys()),
    index=None,
    placeholder="Choose a voice...",
)
voice_id = voice_dict.get(selected_voice_label) if selected_voice_label else None

# Advance Dropdown (Collapsible) for Speed & Pitch
with st.expander("⚙️ Advance", expanded=False):
  col1, col2 = st.columns(2)
  with col1:
    rate_val = st.slider(
        "Speed Rate (%)", min_value=-50, max_value=50, value=0, step=5
    )
  with col2:
    pitch_val = st.slider(
        "Pitch Shift (Hz)", min_value=-20, max_value=20, value=0, step=1
    )

generate_srt = st.checkbox(
    "Generate Synchronized SRT Subtitles (.srt)", value=True
)

if st.button(
    "🚀 Generate Voice & Files", type="primary", use_container_width=True
):
  if not text_input.strip():
    st.warning("Please enter some text in the box first.")
  elif not selected_language or not voice_id:
    st.warning("Please select both a Language and a Voice first.")
  else:
    try:
      with st.spinner("Generating audio and export formats..."):
        audio_file, srt_file, txt_file = loop.run_until_complete(
            generate_tts(
                text_input, voice_id, rate_val, pitch_val, generate_srt
            )
        )

        st.success("Success! Audio and files generated successfully.")

        # Play Audio
        st.audio(audio_file, format="audio/mp3")

        st.markdown("### 📥 Download Export Formats")
        dcol1, dcol2, dcol3 = st.columns(3)

        with dcol1:
          with open(audio_file, "rb") as f:
            st.download_button(
                label="📥 Download MP3",
                data=f,
                file_name="vexon_output.mp3",
                mime="audio/mp3",
            )

        with dcol2:
          with open(txt_file, "r", encoding="utf-8") as f:
            st.download_button(
                label="📥 Download Script TXT",
                data=f,
                file_name="vexon_script.txt",
                mime="text/plain",
            )

        with dcol3:
          if srt_file:
            with open(srt_file, "r", encoding="utf-8") as f:
              st.download_button(
                  label="📥 Download Subtitles SRT",
                  data=f,
                  file_name="vexon_subtitles.srt",
                  mime="text/plain",
              )
    except Exception:
      st.error(
          "Service is temporarily busy. Please try again in a few seconds."
      )
