import asyncio
import os
import re
import tempfile
import edge_tts
import streamlit as st

# Page Configuration (Removes Get Help, Report a Bug, and About from 3-dot menu, keeping Settings/Theme)
st.set_page_config(
    page_title="Vexon Voice Studio",
    page_icon="🎙️",
    layout="centered",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None,
    },
)

# Custom CSS for Sticky Sleek Header, Hiding GitHub/Share, and Security
st.markdown(
    """
    <style>
    /* Make top Streamlit header transparent so 3-dot menu stays clickable */
    header[data-testid="stHeader"] {
        background: transparent !important;
        z-index: 100001 !important;
    }

    /* Hide GitHub icon, Share button, Star, and Deploy buttons */
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

    /* Sleek Fixed/Sticky Branding Bar at the very top */
    .vexon-sticky-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 56px;
        background: linear-gradient(90deg, #1e1b4b 0%, #311042 50%, #1e1b4b 100%);
        border-bottom: 1px solid rgba(168, 85, 247, 0.35);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 99999;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        padding: 0 50px;
    }

    .vexon-sticky-header h2 {
        color: #c084fc;
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: 1px;
        white-space: nowrap;
    }

    .vexon-sticky-header span {
        color: #e5e7eb;
        font-size: 0.85rem;
        font-weight: 400;
        margin-left: 10px;
    }

    /* Adjust main content padding so it doesn't hide under the fixed header */
    .block-container {
        padding-top: 75px !important;
    }

    @media (max-width: 600px) {
        .vexon-sticky-header span {
            display: none;
        }
        .vexon-sticky-header h2 {
            font-size: 1.1rem;
        }
    }
    </style>

    <div class="vexon-sticky-header">
        <h2>🎙️ VEXON Voice Studio <span>| AI Text-to-Speech</span></h2>
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
    text = re.sub(rf"\b{word}\b", "", text, flags=re.IGNORECASE)
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

# Smart Search Bar with requested placeholder
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
