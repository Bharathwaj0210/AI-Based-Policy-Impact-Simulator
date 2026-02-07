import streamlit as st
import pandas as pd
import numpy as np
import shap
import matplotlib.pyplot as plt
import joblib

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Government Policy Impact Simulator",
    layout="wide"
)

st.title("📊 Government Policy Impact Simulator")
st.write(
    "Upload a government policy dataset. "
    "The system aligns columns automatically, "
    "predicts eligibility, explains decisions using SHAP, "
    "and recommends optimal policy conditions using ML."
)

# =====================================================
# LOAD MODEL ASSETS
# =====================================================
@st.cache_resource
def load_artifacts():
    pipeline = joblib.load(
        r"C:\Users\saib4\Desktop\Policy scheme\models\government_policy_model.pkl"
    )
    required_features = joblib.load(
        r"C:\Users\saib4\Desktop\Policy scheme\models\required_features.pkl"
    )
    column_aliases = joblib.load(
        r"C:\Users\saib4\Desktop\Policy scheme\models\column_aliases.pkl"
    )
    return pipeline, required_features, column_aliases

pipeline, REQUIRED_FEATURES, COLUMN_ALIASES = load_artifacts()

st.success("✅ Model loaded successfully")

# =====================================================
# ALIAS HANDLING
# =====================================================
def apply_aliases(df, aliases):
    df = df.copy()
    for canonical, variants in aliases.items():
        for v in variants:
            v = v.lower()
            if v in df.columns and canonical not in df.columns:
                df.rename(columns={v: canonical}, inplace=True)
    return df

# =====================================================
# NORMALIZE & ALIGN DATA
# =====================================================
def normalize_and_align(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()

    df = apply_aliases(df, COLUMN_ALIASES)

    for col in REQUIRED_FEATURES:
        if col not in df.columns:
            df[col] = np.nan

    for col in df.columns:
        if df[col].dtype != "object":
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median())

    for col in df.select_dtypes(include="object"):
        df[col] = df[col].fillna("unknown").astype(str)

    return df[REQUIRED_FEATURES]

# =====================================================
# POLICY OPTIMIZATION ENGINE (ML-DRIVEN)
# =====================================================
def recommend_optimal_policy(df, base_rate):
    best_score = base_rate
    best_policy = None

    age_ranges = [(18, 60), (21, 55), (25, 50)]
    income_limits = [30000, 50000, 70000]
    family_limits = [0, 1, 2]
    residence_opts = ["All", "Urban", "Rural"]

    for min_age, max_age in age_ranges:
        for income in income_limits:
            for family in family_limits:
                for res in residence_opts:

                    temp = df.copy()

                    if "age" in temp.columns:
                        temp = temp[
                            (temp["age"] >= min_age) &
                            (temp["age"] <= max_age)
                        ]

                    if "income" in temp.columns:
                        temp = temp[temp["income"] <= income]

                    if "family_members" in temp.columns:
                        temp = temp[temp["family_members"] >= family]

                    if res != "All" and "residence_type" in temp.columns:
                        temp = temp[
                            temp["residence_type"].str.lower() == res.lower()
                        ]

                    if len(temp) < 10:
                        continue

                    score = temp["predicted_eligibility"].mean()

                    if score > best_score + 0.03:
                        best_score = score
                        best_policy = {
                            "Age Range": f"{min_age} – {max_age}",
                            "Max Income": income,
                            "Min Family Members": family,
                            "Residence": res
                        }

    return best_policy, best_score

# =====================================================
# FILE UPLOAD
# =====================================================
uploaded_file = st.file_uploader(
    "📤 Upload Government Policy Dataset (CSV)",
    type=["csv"]
)

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.subheader("📁 Uploaded Dataset Preview")
    st.dataframe(df.head())

    # ================================
    # ALIGN DATA
    # ================================
    X = normalize_and_align(df)

    probs = pipeline.predict_proba(X)[:, 1]
    df["eligibility_probability"] = probs
    df["predicted_eligibility"] = (probs >= 0.5).astype(int)

    base_rate = df["predicted_eligibility"].mean()

    # ================================
    # METRICS
    # ================================
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Records", len(df))
    c2.metric("Eligible", int(df["predicted_eligibility"].sum()))
    c3.metric("Eligibility Rate", round(base_rate, 2))

    # ================================
    # SCENARIO ANALYSIS
    # ================================
    st.subheader("📈 Scenario Analysis")

    df_sorted = df.sort_values("eligibility_probability")
    n = len(df_sorted)

    best_df = df_sorted.iloc[: int(0.3 * n)]
    avg_df = df_sorted.iloc[int(0.3 * n): int(0.7 * n)]
    worst_df = df_sorted.iloc[int(0.7 * n):]

    scenario_table = pd.DataFrame({
        "Scenario": ["Best", "Average", "Worst"],
        "Records": [len(best_df), len(avg_df), len(worst_df)],
        "Avg Probability": [
            best_df["eligibility_probability"].mean(),
            avg_df["eligibility_probability"].mean(),
            worst_df["eligibility_probability"].mean()
        ]
    })

    st.dataframe(scenario_table)

    # ================================
    # POLICY RECOMMENDATION
    # ================================
    st.subheader("🧠 ML-Recommended Policy")

    best_policy, best_score = recommend_optimal_policy(df, base_rate)

    if best_policy:
        st.success(f"""
**Recommended Policy Conditions**

• Age: {best_policy['Age Range']}
• Max Income: {best_policy['Max Income']}
• Min Family Members: {best_policy['Min Family Members']}
• Residence: {best_policy['Residence']}

📈 Eligibility improves from {base_rate:.2f} → {best_score:.2f}
""")
    else:
        st.info(
            "ℹ️ Current policy is already near optimal. "
            "No alternative policy improves eligibility significantly."
        )

    # ================================
    # SHAP EXPLAINABILITY
    # ================================
    st.subheader("🧠 SHAP Explainability")

    model_only = pipeline.named_steps["model"]
    X_transformed = pipeline.named_steps["preprocessor"].transform(X)

    explainer = shap.TreeExplainer(model_only)
    shap_values = explainer.shap_values(X_transformed)
    shap_matrix = shap_values[1] if isinstance(shap_values, list) else shap_values

    shap.summary_plot(
        shap_matrix,
        X_transformed,
        show=False
    )

    st.pyplot(plt.gcf(), clear_figure=True)

    # ================================
    # DOWNLOAD
    # ================================
    st.subheader("⬇️ Download Results")

    st.download_button(
        "Download Prediction Results",
        df.to_csv(index=False).encode("utf-8"),
        "government_policy_predictions.csv",
        "text/csv"
    )

else:
    st.info("Upload a CSV file to begin.")
