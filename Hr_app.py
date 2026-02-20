import streamlit as st
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import shap
import os
from dotenv import load_dotenv
import google.generativeai as genai

# =============================
# ENV & GEMINI SETUP
# =============================
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-flash-latest")

# =============================
# APP CONFIG
# =============================
st.set_page_config(page_title="HR Policy Simulator", layout="wide")
st.title("🏢 HR Policy Simulator")
st.write("Upload HR data, apply policies, and let the model recommend optimal strategies")

# =============================
# SIDEBAR
# =============================
policy_option = st.sidebar.radio(
    "Choose Policy Simulation",
    ["Recruitment", "Attrition", "Both"]
)

uploaded_file = st.file_uploader("📤 Upload HR Dataset (CSV)", type=["csv"])

# =============================
# REQUIRED FEATURES
# =============================
FEATURES = [
    "Age",
    "TenureYears",
    "Performance Score",
    "Current Employee Rating",
    "IsActive"
]

# =============================
# HELPERS
# =============================
def preprocess_data(df):
    df = df.copy()
    for col in FEATURES:
        if col not in df.columns:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median())
    return df


def plot_shap(model, X):
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    values = shap_values[1] if isinstance(shap_values, list) else shap_values
    shap.summary_plot(values, X, show=False, cmap="Spectral")
    st.pyplot(plt.gcf())
    plt.clf()


def gemini_explain(policy, scenario, df_part):
    try:
        summary = df_part[FEATURES].mean().round(2).to_dict()

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

        return gemini_model.generate_content(prompt).text
    except Exception:
        return "⚠️ Gemini insight unavailable."


# =============================
# MODEL‑DRIVEN POLICY SUGGESTION
# =============================
def suggest_optimal_policy(df, model, score_col, current_filters):
    best_score = df[score_col].mean()
    best_rule = None

    age_vals = [18, 22, 25, 30]
    rating_vals = [2, 3, 4]
    tenure_vals = [1, 3, 5]

    for a in age_vals:
        for r in rating_vals:
            for t in tenure_vals:
                temp = df[
                    (df["Age"] >= a) &
                    (df["Current Employee Rating"] >= r) &
                    (df["TenureYears"] >= t)
                ]

                if len(temp) < 10:
                    continue

                score = temp[score_col].mean()

                if score > best_score + 0.05:
                    best_score = score
                    best_rule = {
                        "Age ≥": a,
                        "Rating ≥": r,
                        "Tenure ≥": t
                    }

    if best_rule is None:
        return "✅ Optimal policy found. Current conditions are effective."

    if best_rule == current_filters:
        return "✅ Optimal policy found. Current conditions match model recommendation."

    rule_text = "🔧 **Model‑Suggested Optimal Policy:**\n"
    for k, v in best_rule.items():
        rule_text += f"- {k} {v}\n"

    return rule_text


# =============================
# MAIN
# =============================
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success(f"Dataset loaded ✅ Rows: {df.shape[0]} | Columns: {df.shape[1]}")
    st.dataframe(df.head())

    # =============================
    # USER POLICY CONDITIONS
    # =============================
    st.header("⚙️ User Policy Conditions")

    age_min = st.slider("Minimum Age", 18, 65, 18)
    rating_min = st.slider("Minimum Employee Rating", 1, 5, 1)
    tenure_min = st.slider("Minimum Tenure (Years)", 0, 20, 0)

    user_filters = {
        "Age ≥": age_min,
        "Rating ≥": rating_min,
        "Tenure ≥": tenure_min
    }

    df = df[
        (df["Age"] >= age_min) &
        (df["Current Employee Rating"] >= rating_min) &
        (df["TenureYears"] >= tenure_min)
    ]

    st.info(f"Employees after user conditions: {len(df)}")

    df = preprocess_data(df)
    X = df[FEATURES]

    # =============================
    # MODELS
    # =============================
    if policy_option in ["Recruitment", "Both"]:
        st.header("👥 Recruitment Prediction")
        model = joblib.load("recruitment_policy_model_1.pkl")
        df["Recruitment_Risk_Score"] = model.predict_proba(X)[:, 1]
        plot_shap(model, X)

    if policy_option in ["Attrition", "Both"]:
        st.header("🚪 Attrition Prediction")
        model = joblib.load("attrition_policy_model_1.pkl")
        df["Attrition_Risk_Score"] = model.predict_proba(X)[:, 1]
        plot_shap(model, X)

    # =============================
    # SCENARIO GENERATION
    # =============================
    st.header("📊 Scenario Generation (Data‑Driven)")

    score_col = (
        "Attrition_Risk_Score"
        if policy_option in ["Attrition", "Both"]
        else "Recruitment_Risk_Score"
    )

    df_sorted = df.sort_values(score_col)
    n = len(df_sorted)

    best_df = df_sorted.iloc[:int(0.3 * n)]
    avg_df = df_sorted.iloc[int(0.3 * n):int(0.7 * n)]
    worst_df = df_sorted.iloc[int(0.7 * n):]

    st.info(f"""
**Scenario Split**
- Best Case: {len(best_df)}
- Average Case: {len(avg_df)}
- Worst Case: {len(worst_df)}
- Total: {n}
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

    st.dataframe(selected_df)

    # =============================
    # MODEL‑DRIVEN RECOMMENDATION
    # =============================
    st.header("🧠 Model Policy Recommendation")

    model_used = model
    recommendation = suggest_optimal_policy(
        df_sorted,
        model_used,
        score_col,
        user_filters
    )

    st.write(recommendation)

    # =============================
    # GEMINI EXPLANATION
    # =============================
    st.subheader("🤖 Gemini Scenario Explanation")
    st.write(gemini_explain(policy_option, scenario, selected_df))

else:
    st.info("👆 Upload a CSV file to begin")
