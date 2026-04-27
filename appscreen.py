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
st.caption("Accurate iOS Screen Time Insights")

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
    "Safari": "Productivity",
    "Chrome": "Productivity",
    "ChatGPT": "Productivity"
}

# ---- PREPROCESS (IMPROVED) ----
def preprocess(img):
    img = np.array(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )
    return thresh

# ---- OCR (DUAL PASS) ----
def extract_text(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    text1 = pytesseract.image_to_string(gray, config='--oem 3 --psm 4')
    processed = preprocess(image)
    text2 = pytesseract.image_to_string(processed, config='--oem 3 --psm 4')

    return text1 if len(text1) > len(text2) else text2

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

# ---- TOTAL TIME ----
def extract_total_time(text):
    match = re.search(r"(\d+)\s*h\s*(\d+)?\s*m", text)
    if match:
        h = int(match.group(1))
        m = int(match.group(2)) if match.group(2) else 0
        return round(h + m/60, 2)
    return None

# ---- MOST USED PARSER ----
def parse_most_used(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    KNOWN_APPS = list(CATEGORY_MAP.keys())
    data = []

    for i, line in enumerate(lines):
        for app in KNOWN_APPS:
            if app.lower() in line.lower():

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

# ---- PRODUCTIVITY SCORE ----
def productivity_score(df, pickups):
    score = 100

    # penalize addictive apps
    for _, row in df.iterrows():
        if row["Category"] in ["Social", "Gaming"] and row["Hours"] > 0.5:
            score -= 10

    # pickups penalty
    if pickups > 80:
        score -= 20
    elif pickups > 50:
        score -= 10

    return max(score, 0)

# ---- UI ----
st.markdown("## 📊 Upload Screenshots")

colA, colB = st.columns(2)

with colA:
    overview_img = st.file_uploader("📈 Screen Time Overview", type=["png","jpg","jpeg"])

with colB:
    apps_img = st.file_uploader("📱 Most Used Apps", type=["png","jpg","jpeg"])

# ---- PICKUPS INPUT ----
st.markdown("## 📱 Daily Pickups")
pickups = st.number_input("Enter number of times you picked your phone today", 0, 300, 40)

# ---- PROCESS ----
if overview_img and apps_img:

    img1 = Image.open(overview_img)
    img2 = Image.open(apps_img)

    col1, col2 = st.columns(2)
    with col1:
        st.image(img1, width=250)
    with col2:
        st.image(img2, width=250)

    text1 = extract_text(img1)
    text2 = extract_text(img2)

    total_time = extract_total_time(text1)
    df = parse_most_used(text2)

    if not df.empty:

        df["Category"] = df["App"].apply(lambda x: CATEGORY_MAP.get(x, "Other"))

        st.markdown("## 📊 Usage Overview")
        st.dataframe(df, use_container_width=True)

        # ---- TOTAL ----
        if total_time:
            st.metric("Total Screen Time", f"{total_time} hrs")

        # ---- CHART ----
        st.markdown("### 📊 App Usage")
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

        # ---- SCORE ----
        score = productivity_score(df, pickups)

        st.markdown("## 🧠 Productivity Score")

        if score > 80:
            st.success(f"🔥 Excellent: {score}/100")
        elif score > 50:
            st.warning(f"⚠️ Moderate: {score}/100")
        else:
            st.error(f"🚨 Poor: {score}/100")

        # ---- INSIGHT ----
        st.markdown("## 🤖 Insight")

        if pickups > 80:
            st.warning("High phone pickups detected. Try reducing frequent checking.")

        if total_time and total_time > DEFAULT_LIMIT:
            st.warning("You exceeded recommended screen time (2.5 hrs).")

        if "Social" in cat and cat["Social"] > 1:
            st.info("High social media usage detected.")

    else:
        st.error("❌ Could not detect apps. Upload clearer 'Most Used' screenshot.")

else:
    st.info("📌 Upload both screenshots to start analysis.")
