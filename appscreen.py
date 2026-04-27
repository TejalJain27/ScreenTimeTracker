import streamlit as st
import pytesseract
import cv2
import numpy as np
from PIL import Image
import re
import os
import pandas as pd
import matplotlib.pyplot as plt
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

# ---- PICKUPS ----
pickups = st.number_input("Daily phone pickups", 0, 300, 40)

# ---- BEHAVIOR QUESTIONS ----
st.markdown("## 🧠 Your Usage Habits")

q1 = st.radio("Do you check your phone without purpose?", ["Yes", "No"])
q2 = st.radio("Do you feel distracted because of phone usage?", ["Yes", "No"])
q3 = st.radio("Do you use your phone before sleeping?", ["Yes", "No"])

# ================= ANALYSIS =================

if len(apps) == 3:

    df = pd.DataFrame({"App": apps, "Hours": hours})

    total_app_usage = sum(hours)

    st.markdown("## 📊 Your Usage")
    st.dataframe(df)

    # ---- ADDICTION SCORE ----
    score = 0

    # usage factor
    if total_app_usage > 3:
        score += 2
    elif total_app_usage > 2:
        score += 1

    # pickups factor
    if pickups > 80:
        score += 2
    elif pickups > 50:
        score += 1

    # behavior factor
    behavior_score = [q1, q2, q3].count("Yes")
    score += behavior_score

    # ---- CLASSIFICATION ----
    if score <= 2:
        level = "Low"
        st.success("✅ Low Risk Usage")
    elif score <= 4:
        level = "Moderate"
        st.warning("⚠️ Moderate Usage — Be Careful")
    else:
        level = "High"
        st.error("🚨 High Risk of Phone Addiction")

    # ---- EXPLANATION ----
    st.markdown("## 🧠 Analysis")

    st.write(f"- Total App Usage: {round(total_app_usage,2)} hrs")
    st.write(f"- Daily Pickups: {pickups}")
    st.write(f"- Behavior Indicators: {behavior_score}/3")

    # ---- ADVICE ----
    st.markdown("## 💡 Suggestions")

    if level == "High":
        st.write("• Set strict app limits")
        st.write("• Avoid phone before sleep")
        st.write("• Keep phone away during work")
    elif level == "Moderate":
        st.write("• Reduce unnecessary usage")
        st.write("• Track daily habits")
    else:
        st.write("• Maintain your healthy habits!")

    # ---- HELPFUL LINKS ----
    st.markdown("## 🌐 Resources")

    st.write("• https://www.digitalwellbeing.org")
    st.write("• https://www.headspace.com")
    st.write("• https://www.rescuetime.com")

