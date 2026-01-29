import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
from dotenv import load_dotenv
import google.generativeai as genai
import matplotlib.pyplot as plt

# =====================================================
# LOAD GEMINI API KEY
# =====================================================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# =====================================================
# PATHS
# =====================================================
MODEL_PATH = r"C:\Users\bharathwaj\Desktop\Mini-Project\policy_rf_model.pkl"
FEATURES_PATH = r"C:\Users\bharathwaj\Desktop\Mini-Project\required_features.pkl"
ALIASES_PATH = r"C:\Users\bharathwaj\Desktop\Mini-Project\column_aliases.pkl"

# =====================================================
# LOAD MODEL
# =====================================================
pipeline = joblib.load(MODEL_PATH)
REQUIRED_FEATURES = joblib.load(FEATURES_PATH)
COLUMN_ALIASES = joblib.load(ALIASES_PATH)

# =====================================================
# DATA UTILITIES
# =====================================================
def normalize_columns(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    return df

def apply_aliases(df):
    df = df.copy()
    for old, new in COLUMN_ALIASES.items():
        if old in df.columns and new not in df.columns:
            df.rename(columns={old: new}, inplace=True)
    return df

def derive_missing_columns(df):
    df = df.copy()
    for col in REQUIRED_FEATURES:
        if col not in df.columns:
            df[col] = "unknown" if col in ["sex", "smoker"] else np.nan

    for col in df.select_dtypes(include="number"):
        df[col] = df[col].fillna(df[col].median())

    for col in df.select_dtypes(include="object"):
        df[col] = df[col].fillna("unknown")

    return df

# =====================================================
# GEMINI SCENARIO GENERATION (SIMPLIFIED OUTPUT)
# =====================================================
def generate_scenarios(summary_text):
    if not GEMINI_API_KEY:
        return None, "Gemini API key not configured"

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
You are an insurance analyst.

Based on the summary below, generate future risk scenarios.

Rules:
- No tables
- No complex words
- Use short bullet points
- Simple business English
- Format strictly as:

Best Case:
- point
- point

Average Case:
- point
- point

Worst Case:
- point
- point

Summary:
{summary_text}
"""

        response = model.generate_content(prompt)
        return response.text.strip(), None

    except Exception as e:
        return None, str(e)

# =====================================================
# STREAMLIT UI
# =====================================================
st.set_page_config("AI-Based Insurance Policy Simulator", layout="wide")
st.title("AI-Based Insurance Policy Simulator with Optimization")

uploaded = st.file_uploader("Upload New Insurance Dataset (CSV)", type=["csv"])

if uploaded:
    df = pd.read_csv(uploaded)
    df = normalize_columns(df)
    df = apply_aliases(df)
    df = derive_missing_columns(df)

    X = df[REQUIRED_FEATURES]

    # ---------------- POLICY RULES ----------------
    st.subheader("Define Policy Conditions")
    max_age = st.slider("Max Age", 18, 80, 60)
    max_bmi = st.slider("Max BMI", 18.0, 50.0, 40.0)
    smoker_allowed = st.selectbox("Smoker Allowed?", ["yes", "no"])

    eligibility_mask = (
        (df["age"] <= max_age)
        & (df["bmi"] <= max_bmi)
        & ((df["smoker"] == smoker_allowed) | (df["smoker"] == "unknown"))
    )

    # ---------------- RISK PREDICTION ----------------
    risk_prob = pipeline.predict_proba(X)[:, 1]
    df["risk_score"] = risk_prob

    # ---------------- METRICS ----------------
    st.subheader("Current Policy Metrics")
    st.metric("Total Records", len(df))
    st.metric("Eligible", eligibility_mask.sum())
    st.metric("Excluded", len(df) - eligibility_mask.sum())
    st.metric("Exclusion Rate (%)", f"{100*(1-eligibility_mask.mean()):.2f}")
    st.metric(
        "Avg Risk (Eligible)",
        f"{df.loc[eligibility_mask,'risk_score'].mean():.3f}"
    )

    # ---------------- RISK DISTRIBUTION ----------------
    st.subheader("Risk Distribution Analysis")

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots()
        ax.hist(df["risk_score"], bins=20)
        ax.set_title("Risk Score Distribution")
        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots()
        ax.boxplot(df["risk_score"], vert=False)
        ax.set_title("Risk Score Spread")
        st.pyplot(fig)

    # =====================================================
    # GEMINI SCENARIOS (BUTTON + CACHED)
    # =====================================================
    st.subheader("Future Risk Scenarios (AI)")

    summary = f"""
Eligibility Rate: {eligibility_mask.mean()*100:.2f}%
Exclusion Rate: {(1-eligibility_mask.mean())*100:.2f}%
Average Risk Score: {df['risk_score'].mean():.3f}
"""

    if "ai_scenarios" not in st.session_state:
        st.session_state.ai_scenarios = None

    if st.button("Generate AI Scenarios"):
        if st.session_state.ai_scenarios is None:
            scenario_text, error = generate_scenarios(summary)
            if error:
                st.error(f"Gemini Error: {error}")
            else:
                st.session_state.ai_scenarios = scenario_text
        else:
            st.info("Using cached AI result")

    if st.session_state.ai_scenarios:
        st.text_area(
            "AI Generated Scenarios",
            st.session_state.ai_scenarios,
            height=260
        )

    # =====================================================
    # POLICY OPTIMIZATION
    # =====================================================
    st.subheader("Optimized Policy Recommendation")

    risk_threshold = np.percentile(risk_prob, 70)
    low_risk_df = df[df["risk_score"] <= risk_threshold]

    opt_age = int(np.percentile(low_risk_df["age"], 90))
    opt_bmi = round(np.percentile(low_risk_df["bmi"], 90), 1)

    opt_smoker = (
        "yes"
        if low_risk_df["smoker"].value_counts(normalize=True).get("yes", 0) > 0.5
        else "no"
    )

    st.success(
        f"""
Recommended Policy:
• Age ≤ {opt_age}
• BMI ≤ {opt_bmi}
• Smoker Allowed: {opt_smoker}
"""
    )

    # =====================================================
    # DOWNLOAD
    # =====================================================
    st.download_button(
        "Download Policy Report",
        df.to_csv(index=False),
        "policy_eligibility_report.csv"
    )

else:
    st.info("Upload a CSV file to start.")
