import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import re
import os
import matplotlib.pyplot as plt

# ---- LOCAL FIX ----
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.set_page_config(page_title="Screen Time Analyzer", layout="wide")

st.title("📱 Screen Time Analyzer")
st.caption("Upload iOS Screen Time + Most Used Apps for accurate insights")

DEFAULT_LIMIT = 2.5

# ---- CATEGORY ----
CATEGORY_MAP = {
    "Instagram": "Social",
    "WhatsApp": "Social",
    "Facebook": "Social",
    "Snapchat": "Social",
    "YouTube": "Entertainment",
    "Call of Duty": "Gaming",
    "PUBG": "Gaming",
    "Safari": "Productivity",
    "Chrome": "Productivity",
    "ChatGPT": "Productivity"
}

# ---- PREPROCESS ----
def preprocess(img):
    img = np.array(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.convertScaleAbs(gray, alpha=1.5)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return thresh

# ---- OCR ----
def extract_text(image):
    processed = preprocess(image)
    config = r'--oem 3 --psm 6'
    return pytesseract.image_to_string(processed, config=config)

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

# ---- PARSE TOTAL TIME ----
def extract_total_time(text):
    match = re.search(r"(\d+)\s*h\s*(\d+)?\s*m", text)
    if match:
        h = int(match.group(1))
        m = int(match.group(2)) if match.group(2) else 0
        return round(h + m/60, 2)
    return None

# ---- PARSE MOST USED ----
def parse_most_used(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    KNOWN_APPS = list(CATEGORY_MAP.keys())
    data = []

    for i, line in enumerate(lines):
        for app in KNOWN_APPS:
            if app.lower() in line.lower():

                # find time nearby
                for j in range(i, min(i+3, len(lines))):
                    if re.search(r"\d", lines[j]):
                        hrs = convert_to_hours(lines[j])
                        if hrs > 0:
                            data.append((app, hrs))
                            break

    df = pd.DataFrame(data, columns=["App", "Hours"])

    if not df.empty:
        df = df.groupby("App", as_index=False)["Hours"].max()

    return df


# ================= UI =================

st.markdown("## 📊 Upload Screenshots")

colA, colB = st.columns(2)

with colA:
    st.markdown("### 1️⃣ Screen Time Overview")
    overview_img = st.file_uploader("Upload Overview", type=["png","jpg","jpeg"], key="overview")

with colB:
    st.markdown("### 2️⃣ Most Used Apps")
    apps_img = st.file_uploader("Upload Most Used", type=["png","jpg","jpeg"], key="apps")


# ---- PROCESS ----
if overview_img and apps_img:

    img1 = Image.open(overview_img)
    img2 = Image.open(apps_img)

    # preview
    col1, col2 = st.columns(2)
    with col1:
        st.image(img1, caption="Overview", width=250)
    with col2:
        st.image(img2, caption="Most Used", width=250)

    # OCR
    text1 = extract_text(img1)
    text2 = extract_text(img2)

    # ---- TOTAL TIME ----
    total_time = extract_total_time(text1)

    # ---- APP DATA ----
    df = parse_most_used(text2)

    if not df.empty:

        df["Category"] = df["App"].apply(lambda x: CATEGORY_MAP.get(x, "Other"))

        st.markdown("## 📊 Usage Overview")
        st.dataframe(df, use_container_width=True)

        # ---- TOTAL ----
        st.markdown("## ⏱ Total Screen Time")
        if total_time:
            st.metric("Total Usage", f"{total_time} hrs")
        else:
            st.warning("Could not detect total time")

        # ---- CHART ----
        st.markdown("### 📊 App Usage Chart")
        fig, ax = plt.subplots()
        ax.bar(df["App"], df["Hours"])
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # ---- CATEGORY ----
        st.markdown("### 📊 Category Usage")
        cat = df.groupby("Category")["Hours"].sum()

        fig2, ax2 = plt.subplots()
        cat.plot(kind="bar", ax=ax2)
        st.pyplot(fig2)

        # ---- PRODUCTIVITY SCORE ----
        score = 100
        for _, row in df.iterrows():
            if row["Category"] in ["Social", "Gaming"] and row["Hours"] > 0.5:
                score -= 10

        st.markdown("## 🧠 Productivity Score")

        if score > 80:
            st.success(f"🔥 Excellent: {score}/100")
        elif score > 50:
            st.warning(f"⚠️ Moderate: {score}/100")
        else:
            st.error(f"🚨 Poor: {score}/100")

        # ---- FINAL INSIGHT ----
        st.markdown("## 🤖 Insight")

        if total_time and total_time > DEFAULT_LIMIT:
            st.warning("⚠️ You exceeded recommended 2.5 hrs usage")

        if "Social" in cat and cat["Social"] > 1:
            st.info("You are spending a lot of time on social apps")

    else:
        st.error("❌ Could not detect apps from second image. Try clearer 'Most Used' screenshot.")

else:
    st.info("📌 Upload both screenshots to begin analysis")
