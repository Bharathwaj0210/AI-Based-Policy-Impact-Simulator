import streamlit as st
import pandas as pd
import numpy as np
import joblib
import shap
import os
import json
from dotenv import load_dotenv
from google import genai

# ------------------------
# Load ENV
# ------------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

# ------------------------
# Load model
# ------------------------
MODEL_PATH = r"C:\Users\DAKSHANAMURTHI\Downloads\policy_simulator\hr_policy_model.pkl"
model = joblib.load(MODEL_PATH)

st.set_page_config("AI Policy Simulator", layout="wide")
st.title("🧠 AI-Based HR Policy Impact Simulator")

# ------------------------
# Upload Dataset
# ------------------------
st.header("1️⃣ Upload HR Dataset")

file = st.file_uploader("Upload CSV", type="csv")

if file:
    df = pd.read_csv(file)
    
    # Normalize column names
    df.columns = df.columns.str.strip()

    # Calculate Age if missing
    if "Age" not in df.columns and "DOB" in df.columns:
        df["DOB"] = pd.to_datetime(df["DOB"], dayfirst=True)  # dayfirst=True for 07-10-1969 format
        now = pd.Timestamp('now')
        df["Age"] = ((now - df["DOB"]) / pd.Timedelta(days=365.25)).astype(int)
        st.info("Calculated 'Age' from 'DOB' column.")
    elif "Age" not in df.columns:
         st.warning("⚠️ 'Age' and 'DOB' missing. Generating 'Age' from other data...")
         
         if "StartDate" in df.columns:
             # Estimate Age based on StartDate + approx 25 years entry age
             df["StartDate"] = pd.to_datetime(df["StartDate"], dayfirst=True, errors='coerce')
             now = pd.Timestamp('now')
             tenure = ((now - df["StartDate"]) / pd.Timedelta(days=365.25)).fillna(0)
             # Base age 22 + tenure + random variation
             df["Age"] = (22 + tenure + np.random.randint(0, 10, len(df))).astype(int)
             st.info("Estimated 'Age' based on 'StartDate'.")
         else:
             # Random fallback
             df["Age"] = np.random.randint(22, 60, len(df))
             st.warning("Generated synthetic 'Age' (Random 22-60).")
         
             df["Age"] = np.random.randint(22, 60, len(df))
             st.warning("Generated synthetic 'Age' (Random 22-60).")
         
    # Handle missing 'Current Employee Rating'
    if "Current Employee Rating" not in df.columns:
        st.warning("⚠️ 'Current Employee Rating' missing. Generating random ratings (1-5)...")
        df["Current Employee Rating"] = np.random.randint(1, 6, len(df))

    # ------------------------
    # Preprocessing & Feature Engineering
    # ------------------------
    # 1. Generate Policy_Result (Derived Feature expected by model)
    df['Policy_Result'] = df['Current Employee Rating'].apply(lambda x: 1 if x >= 3 else 0)

    # 2. Ensure all model features exist
    if "model" in locals():
        expected_features = model.feature_names_in_
        missing_features = [f for f in expected_features if f not in df.columns]
        
        if missing_features:
            st.warning(f"⚠️ Missing columns: {missing_features}. Filling with synthetic data.")
            for feature in missing_features:
                # Simple heuristic for synthetic data
                if "Code" in feature or "ID" in feature:
                    df[feature] = np.random.randint(0, 2, len(df))
                else:
                    df[feature] = np.random.randint(0, 5, len(df))

        # 3. Label Encoding (Convert objects to numbers as expected by model)
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        for col in expected_features:
            if col in df.columns and df[col].dtype == 'object':
                 df[col] = df[col].astype(str)
                 df[col] = le.fit_transform(df[col])

    st.success("Dataset processed and validated!")
    st.dataframe(df.head())

    # ------------------------
    # Policy Rules
    # ------------------------
    st.header("2️⃣ Define Policy Conditions")

    age_limit = st.slider("Minimum Age", 18, 60, 25)
    rating_limit = st.slider("Minimum Rating", 1, 5, 3)

    df_policy = df[
        (df["Age"] >= age_limit) &
        (df["Current Employee Rating"] >= rating_limit)
    ].copy()

    st.write("Filtered Data:", len(df_policy))

    # ------------------------
    # Prediction
    # ------------------------
    st.header("3️⃣ Model Prediction")

    features = model.feature_names_in_
    X = df_policy[features]

    probs = model.predict_proba(X)[:,1]
    df_policy["Attrition_Risk"] = probs

    st.dataframe(df_policy[["Attrition_Risk"]].head())

    st.metric("Average Risk", round(probs.mean(),3))

    # ------------------------
    # SHAP Explainability
    # ------------------------
    st.header("4️⃣ Explainability (SHAP)")

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # Handle different SHAP return types (list for some models, array for others)
    if isinstance(shap_values, list):
        # Assuming binary classification and we want the positive class (index 1)
        # If it's multi-class, this might need adjustment, but usually index 1 is sufficient for binary.
        shap_data = shap_values[1]
    else:
        # If it returns a single array (e.g., XGBoost binary)
        shap_data = shap_values

    st.write("Feature Importance")
    st.write("Feature Importance")
    import matplotlib.pyplot as plt
    shap.summary_plot(shap_data, X, show=False)
    st.pyplot(plt.gcf())
    plt.clf()

    # ------------------------
    # GEMINI SCENARIOS
    # ------------------------
    st.header("5️⃣ Scenario Generation")

    def generate_scenario(type):
        prompt = f"""
        Generate 200 HR employee records for {type} scenario as JSON list.
        Fields:
        Age (20-60)
        GenderCode (0 or 1)
        PayZone (A,B,C)
        Performance Score (1-5)
        Current Employee Rating (1-5)
        DepartmentType (Sales,Production,IT,HR)

        Return ONLY JSON
        """

        try:
            res = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt
            )
            
            # Clean response (remove markdown code blocks)
            clean_text = res.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
            return pd.DataFrame(data)

        except Exception as e:
            # Handle Quota Limit (429) or other API errors
            # Log full error to console
            print(f"Gemini API Error: {e}")
            # Show friendly message to user
            st.warning("⚠️ AI Limit Reached. Using synthetic data.")
            
            # Fallback: Generate local synthetic data
            np_data = {
                "Age": np.random.randint(20, 61, 200),
                "GenderCode": np.random.randint(0, 2, 200),
                "PayZone": np.random.choice(["A", "B", "C"], 200),
                "Performance Score": np.random.randint(1, 6, 200),
                "Current Employee Rating": np.random.randint(1, 6, 200),
                "DepartmentType": np.random.choice(["Sales", "Production", "IT", "HR"], 200)
            }
            return pd.DataFrame(np_data)

    if st.button("Generate All Scenarios", type="primary"):
        with st.spinner("Generating scenarios..."):
            import time
            df_best = generate_scenario("best case")
            time.sleep(1) # Rate limit handling
            df_avg = generate_scenario("average case")
            time.sleep(1) # Rate limit handling
            df_worst = generate_scenario("worst case")

        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Best Case")
            st.dataframe(df_best.head())
        
        with col2:
            st.subheader("Average Case")
            st.dataframe(df_avg.head())
        
        with col3:
            st.subheader("Worst Case")
            st.dataframe(df_worst.head())

    # ------------------------
    # Policy Recommendation
    # ------------------------
    st.header("6️⃣ AI Policy Recommendation")

    avg_risk = probs.mean()

    if avg_risk > 0.5:
        st.error("""
        ❌ High attrition detected
        ✔ Increase minimum rating
        ✔ Improve incentives
        ✔ Reduce contract hiring
        """)
    else:
        st.success("""
        ✅ Policy is effective
        ✔ Maintain current rules
        ✔ Focus on training
        """)

