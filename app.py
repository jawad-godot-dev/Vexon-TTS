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

# Create a clean mapping for Full Language Names
# Example: en-US -> English (United States) [US] if available or friendly format
locale_map = {}
for v in all_voices:
  loc = v["Locale"]
  # Extract readable name from FriendlyName or Locale
  friendly = v.get("FriendlyName", "")
  if " - " in friendly:
    lang_name = friendly.split(" - ")[0]
  else:
    lang_name = loc
  locale_map[loc] = f"{lang_name} ({loc})"

sorted_locales = sorted(locale_map.keys(), key=lambda x: locale_map[x])


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

# 1. Search filter for Languages / Locales
st.markdown("### 🌐 Language & Voice Selection")
locale_search = st.text_input(
    "🔍 Search Language (e.g. Urdu, English, Arabic, French...)"
).lower()

filtered_locales = [
    loc
    for loc in sorted_locales
    if locale_search in locale_map[loc].lower()
]
if not filtered_locales:
  filtered_locales = sorted_locales  # Fallback if nothing matches

selected_locale = st.selectbox(
    "Select Language / Region",
    filtered_locales,
    format_func=lambda x: locale_map[x],
)

# Filter voices based on selected locale
filtered_voices = [v for v in all_voices if v["Locale"] == selected_locale]
voice_dict = {
    f"{v['FriendlyName']} ({v['Gender']})": v["ShortName"]
    for v in filtered_voices
}

if voice_dict:
  selected_voice_name = st.selectbox(
      "Select Specific AI Voice", list(voice_dict.keys())
  )
  voice_id = voice_dict[selected_voice_name]
else:
  voice_id = "en-US-JennyNeural"

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
