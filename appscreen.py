import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import re
import os
import matplotlib.pyplot as plt

# ---- FIX FOR LOCAL WINDOWS ONLY ----
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.set_page_config(page_title="Screen Time Analyzer", layout="wide")

# ---- HEADER ----
st.title("📱 Screen Time Analyzer")
st.caption("AI-powered iOS Screen Time Insights")

DEFAULT_LIMIT = 2.5

# ---- SUGGESTIONS ----
suggestions = {
    "Instagram": "Limit scrolling. Try 30 min/day.",
    "YouTube": "Avoid binge watching.",
    "WhatsApp": "Mute unnecessary groups.",
    "Safari": "Reduce random browsing.",
    "Snapchat": "Avoid streak pressure.",
    "Facebook": "Avoid passive scrolling.",
    "Chrome": "Focus on productive usage.",
    "Games": "Limit gaming sessions."
}

# ---- IMAGE PREPROCESSING ----
def preprocess_image(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return thresh

# ---- OCR ----
def extract_text(image):
    processed = preprocess_image(image)
    return pytesseract.image_to_string(processed)

# ---- TIME CONVERSION ----
def convert_to_hours(text):
    hours = 0
    h = re.search(r"(\d+)\s*h", text)
    m = re.search(r"(\d+)\s*m", text)

    if h:
        hours += int(h.group(1))
    if m:
        hours += int(m.group(1)) / 60

    return round(hours, 2)

# ---- PARSE iOS DATA ----
def parse_ios(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    apps, times = [], []

    for line in lines:
        if re.search(r"\d+\s*h|\d+\s*m", line):
            times.append(line)
        elif line.isalpha():
            apps.append(line)

    data = []
    for i in range(min(len(apps), len(times))):
        data.append((apps[i], convert_to_hours(times[i])))

    return pd.DataFrame(data, columns=["App", "Hours"])


# ---- PRODUCTIVITY SCORE ----
def productivity_score(df, limits):
    score = 100
    for _, row in df.iterrows():
        if row["Hours"] > limits[row["App"]]:
            score -= 10
    return max(score, 0)


# ---- FILE UPLOAD ----
st.markdown("### 📷 Upload Screenshot")
uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg"])

if uploaded_file:

    image = Image.open(uploaded_file)

    # ---- CENTERED IMAGE ----
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image(image, caption="Preview", width=300)

    # ---- OCR ----
    text = extract_text(image)

    with st.expander("🔍 View Extracted Text"):
        st.text(text)

    df = parse_ios(text)

    if not df.empty:

        st.markdown("## 📊 Usage Overview")
        st.dataframe(df, use_container_width=True)

        # ---- LIMIT SETTINGS ----
        st.markdown("## ⚙️ Customize Limits")

        limits = {}
        for _, row in df.iterrows():
            limits[row["App"]] = st.slider(
                f"{row['App']} limit (hrs)",
                0.5, 10.0, DEFAULT_LIMIT
            )

        # ---- ANALYSIS ----
        st.markdown("## 📈 Analysis")

        total_time = df["Hours"].sum()
        st.metric("Total Screen Time", f"{total_time:.2f} hrs")

        # ---- CHART ----
        st.markdown("### 📊 App Usage Chart")

        fig, ax = plt.subplots()
        ax.bar(df["App"], df["Hours"])
        ax.set_ylabel("Hours")
        ax.set_xlabel("Apps")
        plt.xticks(rotation=45)

        st.pyplot(fig)

        # ---- PER APP FEEDBACK ----
        st.markdown("### 📌 App Feedback")

        for _, row in df.iterrows():
            app = row["App"]
            usage = row["Hours"]
            limit = limits[app]

            if usage > limit:
                st.error(f"🚨 {app}: {usage} hrs (Limit {limit})")
                st.write("💡", suggestions.get(app, "Reduce usage gradually."))
            else:
                st.success(f"✅ {app}: Within limit")

        # ---- PRODUCTIVITY SCORE ----
        score = productivity_score(df, limits)

        st.markdown("## 🧠 Productivity Score")

        if score > 80:
            st.success(f"🔥 Excellent: {score}/100")
        elif score > 50:
            st.warning(f"⚠️ Moderate: {score}/100")
        else:
            st.error(f"🚨 Poor: {score}/100")

        # ---- OVERALL ----
        st.markdown("## 🧾 Overall Feedback")

        if total_time > DEFAULT_LIMIT:
            st.warning("⚠️ You exceeded 2.5 hrs total usage")
        else:
            st.success("👍 Healthy screen usage")

        # ---- GENERAL TIPS ----
        st.markdown("## 📌 Tips to Improve")

        tips = [
            "Use Screen Time limits in iOS settings",
            "Enable Downtime",
            "Turn off notifications",
            "Keep phone away during work",
            "Switch to grayscale mode"
        ]

        for tip in tips:
            st.write("•", tip)

    else:
        st.error("❌ Could not detect apps. Try a clearer iOS screenshot.")
