import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import re
import os
import matplotlib.pyplot as plt

# ---- LOCAL WINDOWS FIX ----
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.set_page_config(page_title="Screen Time Analyzer", layout="wide")

st.title("📱 Screen Time Analyzer")
st.caption("Smart iOS Screen Time Insights")

DEFAULT_LIMIT = 2.5

# ---- CATEGORY MAP ----
CATEGORY_MAP = {
    "Instagram": "Social",
    "WhatsApp": "Social",
    "Facebook": "Social",
    "Snapchat": "Social",
    "YouTube": "Entertainment",
    "Call of Duty": "Gaming",
    "PUBG": "Gaming",
    "Chrome": "Productivity",
    "Safari": "Productivity",
    "ChatGPT": "Productivity"
}

SUGGESTIONS = {
    "Social": "Reduce scrolling. Try app timers.",
    "Gaming": "Limit sessions. Take breaks.",
    "Entertainment": "Avoid binge watching.",
    "Productivity": "Good usage. Keep it up!"
}

# ---- IMAGE PREPROCESS ----
def preprocess(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.convertScaleAbs(gray, alpha=1.5)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return thresh

# ---- OCR ----
def extract_text(image):
    processed = preprocess(image)
    config = r'--oem 3 --psm 6'
    return pytesseract.image_to_string(processed, config=config)

# ---- TIME PARSER ----
def convert_to_hours(text):
    h = re.search(r"(\d+)\s*h", text)
    m = re.search(r"(\d+)\s*m", text)

    hours = 0
    if h:
        hours += int(h.group(1))
    if m:
        hours += int(m.group(1)) / 60

    return round(hours, 2)

# ---- HYBRID PARSER ----
def parse_ios(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    KNOWN_APPS = [
        "Instagram", "WhatsApp", "ChatGPT", "Call of Duty",
        "YouTube", "Facebook", "Snapchat", "Safari", "Chrome"
    ]

    data = []

    for i, line in enumerate(lines):
        for app in KNOWN_APPS:
            if app.lower() in line.lower():

                for j in range(i, min(i+3, len(lines))):
                    if re.search(r"\d", lines[j]):
                        hours = convert_to_hours(lines[j])
                        if hours > 0:
                            data.append((app, hours))
                            break

    df = pd.DataFrame(data, columns=["App", "Hours"])

    if not df.empty:
        df = df.groupby("App", as_index=False)["Hours"].max()

    return df

# ---- PRODUCTIVITY SCORE ----
def productivity_score(df):
    score = 100
    for _, row in df.iterrows():
        category = CATEGORY_MAP.get(row["App"], "Social")
        if category in ["Social", "Gaming"] and row["Hours"] > 0.5:
            score -= 10
    return max(score, 0)

# ---- AI SUMMARY ----
def generate_summary(df):
    total = df["Hours"].sum()
    summary = f"Total usage: {round(total,2)} hrs.\n"

    social_time = df[df["App"].map(CATEGORY_MAP).eq("Social")]["Hours"].sum()

    if social_time > 1:
        summary += "High social media usage detected.\n"

    if total > 2.5:
        summary += "Overall screen time is above recommended limit.\n"
    else:
        summary += "Screen usage looks balanced.\n"

    return summary

# ---- UI ----
st.markdown("### 📷 Upload Screenshot")
file = st.file_uploader("", type=["png", "jpg", "jpeg"])

if file:
    image = Image.open(file)

    # Center image
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image(image, width=300)

    text = extract_text(image)

    with st.expander("🔍 View Extracted Text"):
        st.text(text)

    df = parse_ios(text)

    # ---- FALLBACK ----
    if df.empty:
        st.warning("⚠️ Couldn't auto-detect apps.")

        manual = st.text_area("Enter manually (e.g. Instagram 40m, WhatsApp 20m)")

        if manual:
            parsed = []
            entries = manual.split(",")

            for entry in entries:
                parts = entry.strip().split()
                if len(parts) >= 2:
                    app = parts[0]
                    time = convert_to_hours(" ".join(parts[1:]))
                    parsed.append((app, time))

            df = pd.DataFrame(parsed, columns=["App", "Hours"])

    if not df.empty:

        df["Category"] = df["App"].apply(lambda x: CATEGORY_MAP.get(x, "Social"))

        st.markdown("## 📊 Usage Overview")
        st.dataframe(df, use_container_width=True)

        # ---- APP CHART ----
        st.markdown("### 📊 App Usage")
        fig, ax = plt.subplots()
        ax.bar(df["App"], df["Hours"])
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # ---- CATEGORY CHART ----
        st.markdown("### 📊 Category Usage")
        cat_df = df.groupby("Category")["Hours"].sum()

        fig2, ax2 = plt.subplots()
        cat_df.plot(kind="bar", ax=ax2)
        st.pyplot(fig2)

        # ---- SCORE ----
        score = productivity_score(df)

        st.markdown("## 🧠 Productivity Score")

        if score > 80:
            st.success(f"🔥 Excellent: {score}/100")
        elif score > 50:
            st.warning(f"⚠️ Moderate: {score}/100")
        else:
            st.error(f"🚨 Poor: {score}/100")

        # ---- SUMMARY ----
        st.markdown("## 🤖 AI Insight")
        st.info(generate_summary(df))

        # ---- TIPS ----
        st.markdown("## 📌 Suggestions")
        for cat in df["Category"].unique():
            st.write(f"**{cat}:** {SUGGESTIONS.get(cat)}")

    else:
        st.error("❌ No data available. Please input manually.")
