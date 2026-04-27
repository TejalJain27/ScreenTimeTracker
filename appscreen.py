import streamlit as st
import pytesseract
import cv2
import numpy as np
from PIL import Image
import re
import os
import pandas as pd
import matplotlib.pyplot as plt

# ---- FIX FOR WINDOWS ----
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.set_page_config(page_title="Screen Time Analyzer", layout="wide")

st.title("📱 Screen Time Analyzer")
st.caption("Behavior-based Digital Wellbeing Analyzer")

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

def extract_total_time(text):
    match = re.search(r"(\d+)\s*h\s*(\d+)?\s*m", text)
    if match:
        h = int(match.group(1))
        m = int(match.group(2)) if match.group(2) else 0
        return round(h + m/60, 2)
    return None

# ================= UI =================

# ---- SCREEN TIME UPLOAD ----
st.markdown("## 📊 Upload Screen Time Screenshot")
img_file = st.file_uploader("Upload Screenshot", type=["png","jpg","jpeg"])

total_time = None

if img_file:
    image = Image.open(img_file)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image(image, width=300)

    text = extract_text(image)
    total_time = extract_total_time(text)

    if total_time:
        hours_int = int(total_time)
        minutes = int((total_time - hours_int) * 60)

        st.success(f"⏱ Total Screen Time: {hours_int}h {minutes}m ({round(total_time,2)} hrs)")
        st.caption("Decimal format is used internally for analysis")
    else:
        st.warning("Could not detect total screen time")

# ---- MANUAL APP INPUT ----
st.markdown("## 📱 Enter Top 3 Most Used Apps")

apps = []
hours = []

for i in range(3):
    col1, col2 = st.columns(2)
    with col1:
        app = st.text_input(f"App {i+1}", key=f"app_{i}")
    with col2:
        time = st.text_input(f"Usage (e.g. 1h 30m)", key=f"time_{i}")

    if app and time:
        apps.append(app)
        hours.append(convert_to_hours(time))

# ---- CUSTOM LIMIT ----
st.markdown("## ⚙️ Set Usage Limit")
limit = st.slider("Daily app usage limit (hrs)", 0.5, 5.0, 2.0, 0.5)

# ---- PICKUPS ----
st.markdown("## 📱 Daily Pickups")
pickups = st.number_input("How many times did you pick your phone?", 0, 300, 40)

# ---- BEHAVIOR QUESTIONS ----
st.markdown("## 🧠 Your Usage Habits")

q1 = st.radio("Do you check your phone without purpose?", ["Yes", "No"])
q2 = st.radio("Do you feel distracted due to phone usage?", ["Yes", "No"])
q3 = st.radio("Do you use your phone before sleeping?", ["Yes", "No"])

# ================= ANALYSIS =================

if len(apps) == 3:

    df = pd.DataFrame({"App": apps, "Hours": hours})
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
    st.markdown(f"## ⚠️ High Usage Apps (> {limit} hrs)")
    high_usage = df[df["Hours"] > limit]

    if not high_usage.empty:
        for _, row in high_usage.iterrows():
            st.error(f"{row['App']} → {row['Hours']} hrs")
    else:
        st.success(f"No apps exceed {limit} hrs 🎉")

    # ---- CONSISTENCY ----
    if total_time:
        entered_total = sum(hours)

        st.markdown("## 🔍 Consistency Check")
        st.write(f"Entered Apps Total: {round(entered_total,2)} hrs")

        if abs(entered_total - total_time) > 0.5:
            st.warning("App usage does not match total screen time (missing apps)")
        else:
            st.success("App usage matches total screen time")

    # ---- ADDICTION SCORE ----
    score = 0

    if sum(hours) > 3:
        score += 2
    elif sum(hours) > 2:
        score += 1

    if pickups > 80:
        score += 2
    elif pickups > 50:
        score += 1

    score += [q1, q2, q3].count("Yes")

    st.markdown("## 🧠 Addiction Analysis")

    if score <= 2:
        st.success("✅ Low Risk Usage")
    elif score <= 4:
        st.warning("⚠️ Moderate Usage")
    else:
        st.error("🚨 High Risk of Phone Addiction")

    # ---- INSIGHT ----
    st.markdown("## 🤖 Insights")

    if pickups > 80:
        st.warning("High phone pickups detected")

    if total_time and total_time > DEFAULT_LIMIT:
        st.warning("You exceeded recommended 2.5 hrs usage")

    # ---- RESOURCES ----
    st.markdown("## 🌐 Helpful Resources")

    st.write("• https://www.digitalwellbeing.org")
    st.write("• https://www.headspace.com")
    st.write("• https://www.rescuetime.com")
