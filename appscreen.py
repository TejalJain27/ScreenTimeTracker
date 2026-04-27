import streamlit as st
import pytesseract
import cv2
import numpy as np
from PIL import Image
import re
import os
import pandas as pd
import matplotlib.pyplot as plt

# ---- WINDOWS FIX ----
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.set_page_config(page_title="Screen Time Analyzer", layout="wide")

st.title("📱 Screen Time Analyzer")
st.caption("Smart Digital Wellbeing Analyzer")

# ---- CATEGORY MAP ----
CATEGORY_MAP = {
    "instagram": "Social",
    "whatsapp": "Social",
    "facebook": "Social",
    "snapchat": "Social",
    "youtube": "Entertainment",
    "call of duty": "Gaming",
    "subway surfers": "Gaming",
    "safari": "Productivity",
    "chrome": "Productivity",
    "chatgpt": "Productivity",
    "spotify": "Music"
}

def get_category(app):
    app = app.lower().strip()
    for key in CATEGORY_MAP:
        if key in app:
            return CATEGORY_MAP[key]
    return "Other"

# ---- OCR ----
def extract_text(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return pytesseract.image_to_string(gray, config='--oem 3 --psm 6')

# ---- TIME FUNCTIONS ----
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
        h = int(total_time)
        m = int((total_time - h) * 60)
        st.success(f"⏱ Total Screen Time: {h}h {m}m ({round(total_time,2)} hrs)")
    else:
        st.warning("Could not detect total time")

# ---- AGE ----
st.markdown("## 👤 Your Profile")
age = st.number_input("Enter your age", 10, 80, value=None, placeholder="Enter age")

def get_avg_usage(age):
    if age < 18:
        return 3.5
    elif age <= 25:
        return 4.5
    elif age <= 40:
        return 3.5
    else:
        return 2.5

if age:
    avg_usage = get_avg_usage(age)
    st.info(f"Average for your age: **{avg_usage} hrs/day**")

# ---- APPS INPUT ----
st.markdown("## 📱 Enter Top 3 Apps")

apps, hours = [], []

for i in range(3):
    col1, col2 = st.columns(2)
    with col1:
        app = st.text_input(f"App {i+1}", key=f"app_{i}")
    with col2:
        time = st.text_input(f"Usage (e.g. 1h 30m)", key=f"time_{i}")

    if app and time:
        apps.append(app)
        hours.append(convert_to_hours(time))

# ---- SETTINGS ----
limit = st.slider("Set app limit (hrs)", 0.5, 5.0, 2.0)
pickups = st.number_input("Daily pickups", 0, 300, 40)

# ================= ANALYSIS =================

if total_time and age and len(apps) == 3:

    df = pd.DataFrame({"App": apps, "Hours": hours})
    df["Category"] = df["App"].apply(get_category)

    st.markdown("## 📊 Your Usage")
    st.dataframe(df)

    # ---- HIGH USAGE ----
    st.markdown(f"## ⚠️ High Usage (> {limit} hrs)")
    high = df[df["Hours"] > limit]

    if not high.empty:
        for _, row in high.iterrows():
            st.error(f"{row['App']} → {row['Hours']} hrs")
    else:
        st.success("All apps within limit 🎉")

    # ---- COMPARISON GRAPH ----
    st.markdown("## 📊 Your Usage vs Average")

    data = pd.DataFrame({
        "Type": ["You", "Average"],
        "Hours": [total_time, avg_usage]
    })

    fig, ax = plt.subplots()
    bars = ax.bar(data["Type"], data["Hours"])

    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x()+bar.get_width()/2, h, f"{round(h,2)}h",
                ha='center', va='bottom')

    st.pyplot(fig)

    # ---- EVALUATION ----
    st.markdown("## 📈 Evaluation")

    diff = round(total_time - avg_usage, 2)

    if diff < -0.5:
        st.success("Low usage — well controlled")
        st.write("Maintain your current habits")

    elif abs(diff) <= 0.5:
        st.info("Average usage")
        st.write("Reduce passive usage slightly")

    else:
        st.warning("High usage detected")

        st.markdown("## 🧠 Habits")

        q1 = st.radio("Check phone without reason?", ["Select","Yes","No"], index=0)
        q2 = st.radio("Feel distracted?", ["Select","Yes","No"], index=0)
        q3 = st.radio("Use before sleep?", ["Select","Yes","No"], index=0)

        if "Select" not in [q1,q2,q3]:

            risk = [q1,q2,q3].count("Yes")

            if risk >= 2:
                st.error("High addiction risk")
            else:
                st.warning("Moderate risk")

    # ---- FINAL REPORT ----
st.markdown("## 🤖 Personalized Report")

# ---- CONTEXTUAL MESSAGE ----
if diff < -0.5:
    advice = "Great job — your screen time is well below average. Maintain this balance and avoid increasing passive usage."

elif abs(diff) <= 0.5:
    advice = "Your usage is around average. Try optimizing by reducing unnecessary scrolling and focusing on meaningful activities."

else:
    advice = "Your usage is higher than average. Consider setting limits, reducing distractions, and avoiding excessive screen time."

st.info(f"""
• Your Usage: {round(total_time,2)} hrs  
• Average: {avg_usage} hrs  
• Difference: {diff} hrs  

👉 {advice}
""")
