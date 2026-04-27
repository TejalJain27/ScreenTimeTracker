import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import re
import os
import matplotlib.pyplot as plt

# ---- FIX FOR LOCAL WINDOWS ----
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.set_page_config(page_title="Screen Time Analyzer", layout="wide")

st.title("📱 Screen Time Analyzer")
st.caption("Smart iOS Screen Time Insights")

DEFAULT_LIMIT = 2.5

# ---- APP CATEGORY CLASSIFICATION ----
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

# ---- SUGGESTIONS ----
SUGGESTIONS = {
    "Social": "Reduce scrolling. Try app timers.",
    "Gaming": "Limit sessions. Take breaks.",
    "Entertainment": "Avoid binge watching.",
    "Productivity": "Good usage. Keep it up!"
}

# ---- PREPROCESS ----
def preprocess(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.convertScaleAbs(gray, alpha=1.5)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return thresh

# ---- OCR ----
def extract_text(image):
    return pytesseract.image_to_string(preprocess(image))

# ---- TIME ----
def convert_to_hours(text):
    h = re.search(r"(\d+)\s*h", text)
    m = re.search(r"(\d+)\s*m", text)

    hours = 0
    if h:
        hours += int(h.group(1))
    if m:
        hours += int(m.group(1)) / 60

    return round(hours, 2)

# ---- SMART PARSER ----
def parse_ios(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    data = []

    capture = False

    for i, line in enumerate(lines):
        if "Most Used" in line:
            capture = True
            continue

        if capture:
            if len(line) > 2 and not re.search(r"\d", line):

                # skip noise words
                if line.lower() in ["show", "categories"]:
                    continue

                app = line

                if i + 1 < len(lines):
                    next_line = lines[i + 1]

                    if re.search(r"\d", next_line):
                        hours = convert_to_hours(next_line)

                        # filter garbage like 'M'
                        if len(app) > 2:
                            data.append((app, hours))

    return pd.DataFrame(data, columns=["App", "Hours"])


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

    category_time = {}

    for _, row in df.iterrows():
        cat = CATEGORY_MAP.get(row["App"], "Social")
        category_time[cat] = category_time.get(cat, 0) + row["Hours"]

    summary = f"Total usage is {round(total,2)} hrs.\n"

    if "Social" in category_time:
        if category_time["Social"] > 1:
            summary += "You are overusing social apps.\n"

    if "Productivity" in category_time:
        summary += "Good productivity usage observed.\n"

    if total > 2.5:
        summary += "Overall screen time is high."

    return summary


# ---- UI ----
st.markdown("### 📷 Upload Screenshot")
file = st.file_uploader("", type=["png", "jpg", "jpeg"])

if file:
    image = Image.open(file)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image(image, width=300)

    text = extract_text(image)

    with st.expander("🔍 View Extracted Text"):
        st.text(text)

    df = parse_ios(text)

    if not df.empty:

        st.success(f"Detected {len(df)} apps ✅")

        # ---- ADD CATEGORY ----
        df["Category"] = df["App"].apply(lambda x: CATEGORY_MAP.get(x, "Social"))

        st.markdown("## 📊 Usage Overview")
        st.dataframe(df, use_container_width=True)

        # ---- CHART ----
        st.markdown("### 📊 App Usage Chart")
        fig, ax = plt.subplots()
        ax.bar(df["App"], df["Hours"])
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # ---- CATEGORY CHART ----
        st.markdown("### 📊 Category-wise Usage")

        cat_df = df.groupby("Category")["Hours"].sum()

        fig2, ax2 = plt.subplots()
        cat_df.plot(kind="bar", ax=ax2)
        st.pyplot(fig2)

        # ---- PRODUCTIVITY SCORE ----
        score = productivity_score(df)

        st.markdown("## 🧠 Productivity Score")

        if score > 80:
            st.success(f"🔥 Excellent: {score}/100")
        elif score > 50:
            st.warning(f"⚠️ Moderate: {score}/100")
        else:
            st.error(f"🚨 Poor: {score}/100")

        # ---- AI SUMMARY ----
        st.markdown("## 🤖 AI Insight")
        st.info(generate_summary(df))

        # ---- TIPS ----
        st.markdown("## 📌 Suggestions")

        for cat in df["Category"].unique():
            st.write(f"**{cat}:** {SUGGESTIONS.get(cat)}")

    else:
        st.error("❌ Could not detect apps. Try a clearer screenshot.")
