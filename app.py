import asyncio
import os
import tempfile
import edge_tts
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Vexon Voice Studio", page_icon="🎙️", layout="centered"
)

# Available prominent voices
VOICES = {
    "English (US) - Jenny (Neural)": "en-US-JennyNeural",
    "English (US) - Guy (Neural)": "en-US-GuyNeural",
    "English (UK) - Sonia (Neural)": "en-GB-SoniaNeural",
    "English (UK) - Ryan (Neural)": "en-GB-RyanNeural",
    "Urdu (Pakistan) - Asad (Neural)": "ur-PK-AsadNeural",
    "Urdu (Pakistan) - Uzma (Neural)": "ur-PK-UzmaNeural",
    "Hindi (India) - Swara (Neural)": "hi-IN-SwaraNeural",
    "Hindi (India) - Madhur (Neural)": "hi-IN-MadhurNeural",
    "Arabic (Saudi Arabia) - Naif (Neural)": "ar-SA-NaifNeural",
    "Arabic (Saudi Arabia) - Zariyah (Neural)": "ar-SA-ZariyahNeural",
}


# Async function for Edge TTS
async def generate_tts(text, voice_id, rate_val, pitch_val, generate_srt):
    rate_str = f"{'+' if rate_val > 0 else ''}{rate_val}%"
    pitch_str = f"{'+' if pitch_val > 0 else ''}{pitch_val}Hz"

    temp_dir = tempfile.mkdtemp()
    audio_path = os.path.join(temp_dir, "vexon_output.mp3")
    srt_path = os.path.join(temp_dir, "vexon_subtitles.srt")

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
                f"{sub_index}\n{format_time(start_time)} --> {format_time(end_time)}\n{word}\n"
            )
            sub_index += 1

    with open(audio_path, "wb") as f:
        f.write(audio_data)

    final_srt_path = None
    if generate_srt and subtitles_content:
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(subtitles_content))
        final_srt_path = srt_path

    return audio_path, final_srt_path


# UI Design
st.markdown(
    """
    <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #1e1b4b, #311042); border-radius: 12px; margin-bottom: 20px;">
        <h1 style="color: #a855f7; margin-bottom: 0;">🎙️ VEXON Voice Studio</h1>
        <p style="color: #9ca3af;">Next-Gen Free AI Text-to-Speech & Subtitle Generator</p>
    </div>
""",
    unsafe_allow_html=True,
)

text_input = st.text_area(
    "Enter Text for Speech",
    value="Welcome to VEXON Voice studio. Create professional voiceovers and synchronized subtitles instantly!",
    height=150,
)

selected_voice_name = st.selectbox(
    "Select AI Voice", list(VOICES.keys())
)
voice_id = VOICES[selected_voice_name]

col1, col2 = st.columns(2)
with col1:
    rate_val = st.slider(
        "Speed Rate (%)", min_for=-50, max_value=50, value=0, step=5
    )
with col2:
    pitch_val = st.slider(
        "Pitch Shift (Hz)", min_value=-20, max_value=20, value=0, step=1
    )

generate_srt = st.checkbox("Generate SRT Subtitles (.srt)", value=True)

if st.button(
    "🚀 Generate Voice & Subtitles",
    type="primary",
    use_container_width=True,
):
    if not text_input.strip():
        st.warning("Please enter some text to generate speech.")
    else:
        with st.spinner("Generating audio and subtitles..."):
            audio_file, srt_file = asyncio.run(
                generate_tts(
                    text_input,
                    voice_id,
                    rate_val,
                    pitch_val,
                    generate_srt,
                )
            )

            st.success("Success! Audio generated successfully.")

            # Play Audio
            st.audio(audio_file, format="audio/mp3")

            # Download Buttons
            with open(audio_file, "rb") as f:
                st.download_button(
                    label="📥 Download MP3 Audio",
                    data=f,
                    file_name="vexon_output.mp3",
                    mime="audio/mp3",
                )

            if srt_file:
                with open(srt_file, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="📥 Download SRT Subtitles",
                        data=f,
                        file_name="vexon_subtitles.srt",
                        mime="text/plain",
                    )
