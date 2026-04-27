import streamlit as st
import pytesseract
import cv2
import numpy as np
from PIL import Image
import re
import os
import pandas as pd
import matplotlib.pyplot as plt

# ---- LOCAL FIX ----
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.set_page_config(page_title="Screen Time Analyzer", layout="wide")

st.title("📱 Screen Time Analyzer")
st.caption("Manual + Smart Screen Time Analysis")

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

# ---- OCR ----
def extract_text(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return pytesseract.image_to_string(gray, config='--oem 3 --psm 6')

# ---- TOTAL TIME ----
def extract_total_time(text):
    match = re.search(r"(\d+)\s*h\s*(\d+)?\s*m", text)
    if match:
        h = int(match.group(1))
        m = int(match.group(2)) if match.group(2) else 0
        return round(h + m/60, 2)
    return None

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

# ================= UI =================

# ---- SCREEN TIME UPLOAD ----
st.markdown("## 📊 Upload Screen Time Screenshot")
img_file = st.file_uploader("Upload Screen Time", type=["png","jpg","jpeg"])

total_time = None

if img_file:
    image = Image.open(img_file)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image(image, width=300)

    text = extract_text(image)
    total_time = extract_total_time(text)

    if total_time:
        st.success(f"⏱ Total Screen Time: {total_time} hrs")
    else:
        st.warning("Could not detect total time")

# ---- MANUAL APP INPUT ----
st.markdown("## ✍️ Add App Usage")

num_apps = st.number_input("Number of apps to enter", 1, 10, 3)

apps = []
hours = []

for i in range(int(num_apps)):
    col1, col2 = st.columns(2)

    with col1:
        app = st.text_input(f"App {i+1} Name", key=f"app_{i}")
    with col2:
        time = st.text_input(f"Usage (e.g. 1h 30m)", key=f"time_{i}")

    if app and time:
        apps.append(app)
        hours.append(convert_to_hours(time))

# ---- DATAFRAME ----
if apps:
    df = pd.DataFrame({
        "App": apps,
        "Hours": hours
    })

    df["Category"] = df["App"].apply(lambda x: CATEGORY_MAP.get(x, "Other"))

    st.markdown("## 📊 Usage Overview")
    st.dataframe(df, use_container_width=True)

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

    # ---- HIGH USAGE ----
    st.markdown("## ⚠️ High Usage Apps (> 2 hrs)")

    high_usage = df[df["Hours"] > 2]

    if not high_usage.empty:
        for _, row in high_usage.iterrows():
            st.error(f"{row['App']} → {row['Hours']} hrs (Too High)")
    else:
        st.success("No apps exceed 2 hrs")

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

    # ---- COMPARISON ----
    if total_time:
        entered_total = sum(df["Hours"])

        st.markdown("## 🔍 Consistency Check")

        st.write(f"Entered Apps Total: {round(entered_total,2)} hrs")

        if abs(entered_total - total_time) > 0.5:
            st.warning("App usage does not match total screen time (possible missing apps)")
        else:
            st.success("App usage matches total screen time")

