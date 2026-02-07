# ============================================================
# GOVERNMENT POLICY IMPACT MODEL – PREDICTION (FINAL FIXED)
# ============================================================

import pandas as pd
import joblib
import os
import numpy as np

# ============================================================
# PATHS (UNCHANGED)
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")

MODEL_PATH = os.path.join(
    MODEL_DIR, r"C:\Users\saib4\Desktop\Policy scheme\models\government_policy_model.pkl"
)
FEATURES_PATH = os.path.join(
    MODEL_DIR, r"C:\Users\saib4\Desktop\Policy scheme\models\required_features.pkl"
)
ALIASES_PATH = os.path.join(
    MODEL_DIR, r"C:\Users\saib4\Desktop\Policy scheme\models\column_aliases.pkl"
)

# ============================================================
# LOAD MODEL ASSETS
# ============================================================

pipeline = joblib.load(MODEL_PATH)
CANONICAL_FEATURES = joblib.load(FEATURES_PATH)
COLUMN_ALIASES = joblib.load(ALIASES_PATH)

# ============================================================
# FEATURE TYPES (CANONICAL ONLY)
# ============================================================

# ✅ USE CANONICAL NAMES ONLY
NUMERIC_COLS = ["age", "income"]

CATEGORICAL_COLS = [
    col for col in CANONICAL_FEATURES if col not in NUMERIC_COLS
]

# ============================================================
# NORMALIZE & ALIGN DATA
# ============================================================

def normalize_and_align(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. Normalize column names
    df.columns = df.columns.str.strip().str.lower()

    # 2. Apply aliases → map dataset names → canonical names
    for canonical, variants in COLUMN_ALIASES.items():
        for variant in variants:
            variant = variant.lower()
            if variant in df.columns and canonical not in df.columns:
                df.rename(columns={variant: canonical}, inplace=True)

    # 3. Ensure all required canonical columns exist
    for col in CANONICAL_FEATURES:
        if col not in df.columns:
            if col in NUMERIC_COLS:
                df[col] = np.nan
            else:
                df[col] = "unknown"

    # 4. Fix numeric columns
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median())

    # 5. Fix categorical columns
    for col in CATEGORICAL_COLS:
        df[col] = df[col].astype(str).fillna("unknown")

    return df[CANONICAL_FEATURES]

# ============================================================
# PREDICTION
# ============================================================

def predict_eligibility(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    X = normalize_and_align(df)

    predictions = pipeline.predict(X)

    df["Predicted_Scheme"] = predictions

    return df

# ============================================================
# RUN TEST
# ============================================================

if __name__ == "__main__":
    result = predict_eligibility(
        r"C:\Users\saib4\Desktop\Policy scheme\test.csv"
    )

    print("✅ Prediction successful")
    print(result[["Predicted_Scheme"]].head())
