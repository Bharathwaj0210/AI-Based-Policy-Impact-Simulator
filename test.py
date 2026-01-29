import streamlit as st
import pandas as pd
import joblib
import json
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

# ----------------------------
# Load model and schema
# ----------------------------
MODEL_PATH = "policy_model.pkl"
SCHEMA_PATH = "schema.json"
ALIASES_PATH = "column_aliases.json"

model = joblib.load(MODEL_PATH)

with open(SCHEMA_PATH, "r") as f:
    schema = json.load(f)

with open(ALIASES_PATH, "r") as f:
    COLUMN_ALIASES = json.load(f)

REQUIRED_FEATURES = schema["features"]
TARGET_COL = schema["target"]

# ----------------------------
# Helper functions
# ----------------------------
def normalize_columns(df):
    df.columns = df.columns.str.strip().str.lower()
    return df

def apply_alias_mapping(df):
    rename_map = {}
    for col in df.columns:
        if col in COLUMN_ALIASES:
            rename_map[col] = COLUMN_ALIASES[col]
    return df.rename(columns=rename_map)

def validate_features(df):
    missing = [col for col in REQUIRED_FEATURES if col not in df.columns]
    return missing

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="AI Policy Impact Simulator", layout="wide")

st.title("AI-Based Policy Impact Simulator – Testing")
st.write("Upload a dataset to test policy approval predictions.")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.subheader("Raw Uploaded Data")
    st.dataframe(df.head())

    # Normalize + alias mapping
    df = normalize_columns(df)
    df = apply_alias_mapping(df)

    # Drop target if exists (for prediction)
    y_true = None
    if TARGET_COL in df.columns:
        y_true = df[TARGET_COL]
        df = df.drop(columns=[TARGET_COL])

    # Drop extra columns
    df_model = df[[col for col in df.columns if col in REQUIRED_FEATURES]]

    # Validate required features
    missing_features = validate_features(df_model)

    if missing_features:
        st.error("❌ Missing required features:")
        st.write(missing_features)
        st.stop()

    st.success("✅ Dataset validated successfully")

    # Prediction
    y_pred = model.predict(df_model)
    y_proba = model.predict_proba(df_model)[:, 1]

    results = df_model.copy()
    results["predicted_policy_approved"] = y_pred
    results["approval_probability"] = y_proba

    st.subheader("Prediction Results")
    st.dataframe(results.head())

    # Metrics (only if ground truth exists)
    if y_true is not None:
        st.subheader("Model Evaluation Metrics")

        cm = confusion_matrix(y_true, y_pred)
        report = classification_report(y_true, y_pred, output_dict=True)
        roc_auc = roc_auc_score(y_true, y_proba)

        st.write("Confusion Matrix")
        st.write(cm)

        st.write("Classification Report")
        st.dataframe(pd.DataFrame(report).transpose())

        st.write(f"ROC-AUC Score: {roc_auc:.4f}")

else:
    st.info("Awaiting CSV upload...")
