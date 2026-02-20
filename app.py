import streamlit as st
import pandas as pd
import numpy as np
import joblib
import shap
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv
import google.generativeai as genai

# =============================
# GEMINI SETUP (STABLE VERSION)
# =============================
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-flash-latest")
# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="HR Policy Simulator", layout="wide")

st.markdown("""
<div style="background-color:black;padding:25px;border-radius:10px;margin-bottom:20px">
<h1 style="color:white;">🏢 HR Policy Simulator</h1>
<p style="color:white;">
Upload HR data, apply policy conditions, and let the model recommend optimal strategy
</p>
</div>
""", unsafe_allow_html=True)

# =============================
# REQUIRED FEATURES
# =============================
REQUIRED_FEATURES = [
    "age",
    "tenureyears",
    "performance score",
    "current employee rating",
    "isactive"
]

# =============================
# REQUIRED COLUMNS POPUP BOX
# =============================
with st.expander("📌 Required Columns (Click to View)", expanded=True):
    st.markdown("""
    ### Your dataset must contain:

    - **age**
    - **tenureyears**
    - **performance score**
    - **current employee rating**
    - **isactive**

    ⚠️ Column names must match exactly (lowercase recommended).
    """)

# =============================
# REQUIRED FEATURES (MODEL TRAINED ON LOWERCASE)
# =============================
REQUIRED_FEATURES = [
    "age",
    "tenureyears",
    "performance score",
    "current employee rating",
    "isactive"
]

# =============================
# SIDEBAR
# =============================
policy_option = st.sidebar.radio(
    "Choose Policy Simulation",
    ["Recruitment", "Attrition"]
)

uploaded_file = st.file_uploader("📤 Upload HR Dataset (CSV)", type=["csv"])

# =============================
# GEMINI FUNCTION
# =============================
def gemini_explain(policy, scenario, df_part):
    if gemini_model is None:
        return "⚠️ Gemini API not configured."

    try:
        summary = df_part[REQUIRED_FEATURES].mean().round(2).to_dict()

        prompt = f"""
You are an HR analytics expert.

Explain the {scenario} scenario for {policy} policy.

Dataset summary:
{summary}

Give 3 short bullet points:
- Risk interpretation
- HR implication
- Action suggestion
"""
        response = gemini_model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"⚠️ Gemini error: {e}"

# =============================
# POLICY RECOMMENDATION
# =============================
def suggest_policy(df, score_col, user_filters):

    base_score = df[score_col].mean()
    best_score = base_score
    best_rule = None

    for age in [18, 22, 25, 30]:
        for rating in [2, 3, 4]:
            for tenure in [0, 1, 3]:

                temp = df[
                    (df["age"] >= age) &
                    (df["current employee rating"] >= rating) &
                    (df["tenureyears"] >= tenure)
                ]

                if len(temp) < 10:
                    continue

                score = temp[score_col].mean()

                # lower risk is better
                if score < best_score - 0.01:
                    best_score = score
                    best_rule = {
                        "Minimum Age": age,
                        "Minimum Rating": rating,
                        "Minimum Tenure": tenure
                    }

    if best_rule is None:
        return None

    if best_rule == user_filters:
        return None

    return best_rule

# =============================
# MAIN
# =============================
if uploaded_file:

    df_original = pd.read_csv(uploaded_file)
    df_original.columns = df_original.columns.str.strip().str.lower()

    st.success(f"Dataset Loaded ✅ Rows: {df_original.shape[0]}")

    # Ensure required features exist
    for col in REQUIRED_FEATURES:
        if col not in df_original.columns:
            df_original[col] = np.random.randint(1, 5, len(df_original))

        df_original[col] = pd.to_numeric(df_original[col], errors="coerce")
        df_original[col] = df_original[col].fillna(df_original[col].median())

    # =============================
    # POLICY CONDITIONS
    # =============================
    st.header("⚙️ Policy Conditions")

    age_min = st.slider("Minimum Age", 18, 65, 18)
    rating_min = st.slider("Minimum Rating", 1, 5, 1)
    tenure_min = st.slider("Minimum Tenure", 0, 20, 0)

    user_filters = {
        "Minimum Age": age_min,
        "Minimum Rating": rating_min,
        "Minimum Tenure": tenure_min
    }

    df = df_original[
        (df_original["age"] >= age_min) &
        (df_original["current employee rating"] >= rating_min) &
        (df_original["tenureyears"] >= tenure_min)
    ].copy()

    st.info(f"Employees after filtering: {len(df)}")

    if len(df) < 10:
        st.warning("Too few records after filtering.")
        st.stop()

    X = df[REQUIRED_FEATURES]

    # =============================
    # LOAD MODEL
    # =============================
    if policy_option == "Recruitment":
        model = joblib.load("recruitment_policy_model.pkl")
        df["Recruitment_Risk_Score"] = model.predict_proba(X)[:, 1]
        score_col = "Recruitment_Risk_Score"
    else:
        model = joblib.load("attrition_policy_model.pkl")
        df["Attrition_Risk_Score"] = model.predict_proba(X)[:, 1]
        score_col = "Attrition_Risk_Score"

    # =============================
    # SHAP
    # =============================
    st.header("🔍 Model Explainability (SHAP)")

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    shap.summary_plot(shap_values, X, show=False)
    st.pyplot(plt.gcf())
    plt.clf()

    # =============================
    # SCENARIO SPLIT
    # =============================
    st.header("📊 Scenario Generation")

    df_sorted = df.sort_values(score_col)
    n = len(df_sorted)

    best_df = df_sorted.iloc[:int(0.3*n)]
    avg_df = df_sorted.iloc[int(0.3*n):int(0.7*n)]
    worst_df = df_sorted.iloc[int(0.7*n):]

    st.info(f"""
Best Case: {len(best_df)}  
Average Case: {len(avg_df)}  
Worst Case: {len(worst_df)}  
Total: {n}
""")

    scenario = st.radio(
        "Select Scenario",
        ["Best Case", "Average Case", "Worst Case"],
        horizontal=True
    )

    selected_df = {
        "Best Case": best_df,
        "Average Case": avg_df,
        "Worst Case": worst_df
    }[scenario]

    # ✅ SHOW ALL ROWS (FIXED)
    st.dataframe(selected_df, use_container_width=True)

    # =============================
    # RECOMMENDATION
    # =============================
    st.header("🧠 Model Recommendation")

    recommendation = suggest_policy(df_sorted, score_col, user_filters)

    if recommendation is None:
        st.success("✅ Current policy is already optimal.")
    else:
        st.warning("🔧 Model Suggested Adjustment:")
        for k, v in recommendation.items():
            st.write(f"- {k}: {v}")

    # =============================
    # GEMINI
    # =============================
    st.subheader("🤖 Gemini Scenario Explanation")
    st.write(gemini_explain(policy_option, scenario, selected_df))

else:
    st.info("👆 Upload a CSV file to begin")