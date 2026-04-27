import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import re

# 🔴 SET PATH (Windows users)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.set_page_config(page_title="Screen Time Analyzer (iOS Ready)", layout="wide")

st.title("📱 Screen Time Analyzer (iOS Friendly)")
st.write("Upload your iPhone Screen Time screenshot")

DEFAULT_LIMIT = 2.5

# ---- SUGGESTIONS ----
suggestions = {
    "Instagram": "Limit scrolling. Try 30 min/day.",
    "YouTube": "Avoid binge watching.",
    "WhatsApp": "Mute unnecessary groups.",
    "Safari": "Reduce random browsing.",
    "Snapchat": "Avoid streak pressure.",
    "Facebook": "Avoid passive scrolling.",
    "Chrome": "Focus on productive usage."
}

# ---- IMAGE PREPROCESSING (IMPORTANT FOR iOS) ----
def preprocess_image(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # increase contrast
    gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)

    # threshold
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    return thresh


# ---- OCR ----
def extract_text(image):
    processed = preprocess_image(image)
    text = pytesseract.image_to_string(processed)
    return text


# ---- TIME PARSER (iOS STYLE) ----
def convert_to_hours(time_str):
    hours = 0

    h_match = re.search(r"(\d+)\s*h", time_str)
    m_match = re.search(r"(\d+)\s*m", time_str)

    if h_match:
        hours += int(h_match.group(1))
    if m_match:
        hours += int(m_match.group(1)) / 60

    return round(hours, 2)


# ---- PARSE iOS SCREEN TIME ----
def parse_ios_screen_time(text):
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    apps = []
    times = []

    for line in lines:
        # detect time patterns
        if re.search(r"\d+\s*h|\d+\s*m", line):
            times.append(line)
        elif line.isalpha():  # app name
            apps.append(line)

    # match apps with times
    data = []
    for i in range(min(len(apps), len(times))):
        app = apps[i]
        hours = convert_to_hours(times[i])
        data.append((app, hours))

    return pd.DataFrame(data, columns=["App", "Hours"])


# ---- UI ----
uploaded_file = st.file_uploader("Upload Screenshot", type=["png", "jpg", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)

    st.image(image, caption="Uploaded Screenshot", use_column_width=True)

    text = extract_text(image)

    with st.expander("🔍 Extracted Raw Text"):
        st.text(text)

    df = parse_ios_screen_time(text)

    if not df.empty:
        st.subheader("📊 Detected Usage")
        st.dataframe(df)

        # ---- CUSTOM LIMITS ----
        st.subheader("⚙️ Customize Limits")

        limits = {}
        for i, row in df.iterrows():
            limits[row["App"]] = st.slider(
                f"{row['App']} Limit (hrs)",
                0.5, 10.0, DEFAULT_LIMIT
            )

        # ---- ANALYSIS ----
        st.subheader("📈 Analysis")

        total_time = df["Hours"].sum()
        st.write(f"⏱ Total Screen Time: **{total_time:.2f} hrs**")

        for i, row in df.iterrows():
            app = row["App"]
            usage = row["Hours"]
            limit = limits[app]

            if usage > limit:
                st.error(f"🚨 {app}: {usage} hrs (Limit {limit})")
                tip = suggestions.get(app, "Try reducing usage gradually.")
                st.write(f"💡 Tip: {tip}")
            else:
                st.success(f"✅ {app}: {usage} hrs (Within limit)")

        # ---- OVERALL ----
        st.subheader("🧠 Overall Feedback")

        if total_time > DEFAULT_LIMIT:
            st.warning("⚠️ You exceeded 2.5 hrs total usage!")
        else:
            st.success("👍 Healthy usage!")

        # ---- GENERAL TIPS ----
        st.subheader("📌 Tips to Reduce Screen Time")

        tips = [
            "Use Screen Time limits in iOS settings",
            "Enable Downtime mode",
            "Keep phone away while studying",
            "Turn off notifications",
            "Use grayscale mode"
        ]

        for tip in tips:
            st.write("•", tip)

    else:
        st.error("❌ Could not detect apps properly. Try a clear iOS Screen Time screenshot.")