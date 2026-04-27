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

# ---- SCREENSHOT UPLOAD ----
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
    else:
        st.warning("Could not detect total screen time")

# ---- AGE INPUT ----
st.markdown("## 👤 Your Profile")
age = st.number_input("Enter your age", 10, 80, 20)

def get_avg_usage(age):
    if age < 18:
        return 3.5
    elif age <= 25:
        return 4.5
    elif age <= 40:
        return 3.5
    else:
        return 2.5

avg_usage = get_avg_usage(age)

# ---- MANUAL APPS ----
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

# ---- LIMIT ----
st.markdown("## ⚙️ Set Usage Limit")
limit = st.slider("Daily app usage limit (hrs)", 0.5, 5.0, 2.0, 0.5)

# ---- PICKUPS ----
st.markdown("## 📱 Daily Pickups")
pickups = st.number_input("How many times did you pick your phone?", 0, 300, 40)

# ---- BEHAVIOR ----
st.markdown("## 🧠 Your Usage Habits")

q1 = st.radio("Do you check your phone without purpose?", ["Yes", "No"])
q2 = st.radio("Do you feel distracted due to phone usage?", ["Yes", "No"])
q3 = st.radio("Do you use your phone before sleeping?", ["Yes", "No"])

# ================= ANALYSIS =================

if len(apps) == 3:

    df = pd.DataFrame({"App": apps, "Hours": hours})
    df["Category"] = df["App"].apply(lambda x: CATEGORY_MAP.get(x, "Other"))

    st.markdown("## 📊 Your Usage")
    st.dataframe(df, use_container_width=True)

    # ---- HIGH USAGE ----
    st.markdown(f"## ⚠️ High Usage Apps (> {limit} hrs)")
    high_usage = df[df["Hours"] > limit]

    if not high_usage.empty:
        for _, row in high_usage.iterrows():
            st.error(f"{row['App']} → {row['Hours']} hrs")
    else:
        st.success(f"No apps exceed {limit} hrs 🎉")

    # ---- COMPARISON GRAPH ----
    if total_time:
        st.markdown("## 📊 Your Usage vs Average (India)")

        comparison_df = pd.DataFrame({
            "Type": ["You", "Average"],
            "Hours": [total_time, avg_usage]
        })

        fig, ax = plt.subplots()
        ax.bar(comparison_df["Type"], comparison_df["Hours"])
        ax.set_ylabel("Hours")
        st.pyplot(fig)

        # ---- INSIGHT ----
        st.markdown("## 📈 Comparison Insight")

        if total_time > avg_usage:
            st.warning("⚠️ Your screen time is higher than average for your age group.")
        elif total_time < avg_usage:
            st.success("✅ Your screen time is lower than average.")
        else:
            st.info("Your usage is around average.")

    # ---- ADDICTION ANALYSIS ----
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

    # ---- INSIGHTS ----
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
