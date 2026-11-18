import asyncio
import os
import tempfile
import edge_tts
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Vexon Voice Studio", page_icon="🎙️", layout="centered"
)


# Fetch all available voices dynamically from Edge-TTS
@st.cache_data
async def get_all_voices():
  voices = await edge_tts.list_voices()
  return voices


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
all_voices = loop.run_until_complete(get_all_voices())


# Format voices cleanly: Language (Country) - Voice Name (Gender)
def clean_voice_display(v):
  locale = v.get("Locale", "")  # e.g., ur-PK
  gender = v.get("Gender", "Unknown")
  short_name = v.get("ShortName", "")  # e.g., ur-PK-AsadNeural
  friendly = v.get("FriendlyName", "")  # e.g., Microsoft Asad (Urdu, Pakistan)

  # Extract voice name cleanly
  parts = short_name.split("-")
  voice_name = parts[-1].replace("Neural", "") if len(parts) >= 3 else "Voice"

  # Extract Language and Country details cleanly from FriendlyName or Locale
  if "(" in friendly and ")" in friendly:
    # e.g. "Microsoft Asad (Urdu, Pakistan)" -> extracts "(Urdu, Pakistan)"
    start = friendly.find("(")
    end = friendly.rfind(")")
    lang_country = friendly[start + 1 : end]
  else:
    lang_country = locale

  return f"{lang_country} - {voice_name} ({gender})"


# Prepare rich list of voices with clean display names
voice_options = []
for v in all_voices:
  display_name = clean_voice_display(v)
  voice_options.append({"display": display_name, "id": v["ShortName"], "raw": v})


# Async function for Edge TTS generation
async def generate_tts(
    text, voice_id, rate_val, pitch_val, generate_srt
):
  if rate_val == 0:
    rate_str = "+0%"
  else:
    rate_str = f"{rate_val:+d}%"

  if pitch_val == 0:
    pitch_str = "+0Hz"
  else:
    pitch_str = f"{pitch_val:+d}Hz"

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


# UI Design
st.markdown(
    """
    <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #1e1b4b, #311042); border-radius: 12px; margin-bottom: 20px;">
        <h1 style="color: #a855f7; margin-bottom: 0;">🎙️ VEXON Voice Studio</h1>
        <p style="color: #9ca3af;">Next-Gen Free AI Text-to-Speech & Multi-Format Downloader</p>
    </div>
""",
    unsafe_allow_html=True,
)

text_input = st.text_area(
    "Enter Text for Speech",
    value=(
        "Welcome to VEXON Voice studio. Create professional voiceovers and"
        " synchronized subtitles instantly!"
    ),
    height=150,
)

# Search System with Search Button
st.markdown("### 🔍 Global Voice & Language Search")

col_search, col_btn = st.columns([3, 1])
with col_search:
  search_query = st.text_input(
      "Search by Language, Country, or Voice Name",
      value="",
      placeholder="e.g. Urdu, Jenny, Asad...",
      label_visibility="collapsed",
  )
with col_btn:
  search_clicked = st.button(
      "🔎 Search", use_container_width=True, type="secondary"
  )

# Filter options based on search query
if search_query.strip():
  query = search_query.lower()
  filtered_options = [
      opt for opt in voice_options if query in opt["display"].lower()
  ]
  if not filtered_options:
    filtered_options = voice_options
    st.warning("No matching voices found. Showing all voices.")
else:
  filtered_options = voice_options

# Dropdown showing clean results
display_to_id = {opt["display"]: opt["id"] for opt in filtered_options}
selected_display_name = st.selectbox(
    "Select Voice & Language Result", list(display_to_id.keys())
)
voice_id = display_to_id[selected_display_name]

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
    st.warning("Please enter some text to generate speech.")
  else:
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
