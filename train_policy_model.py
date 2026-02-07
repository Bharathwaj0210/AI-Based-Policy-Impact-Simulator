# ============================================================
# GOVERNMENT POLICY ELIGIBILITY MODEL - TRAINING
# ============================================================

import pandas as pd
import numpy as np
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
from sklearn.ensemble import RandomForestClassifier

# ============================================================
# CONFIGURATION
# ============================================================

DATASET_PATH = r"C:\Users\saib4\Desktop\Policy scheme\gov_eligibility_dataset.csv"
MODEL_DIR = r"C:\Users\saib4\Desktop\Policy scheme\models"

os.makedirs(MODEL_DIR, exist_ok=True)

TARGET_COLUMN = "eligible"

CANONICAL_FEATURES = [
    "age",
    "income",
    "employment_status",
    "education_level",
    "residence_type",
    "social_category",
    "gender",
    "disability_status",
    "family_members"
]

COLUMN_ALIASES = {
    "age": ["age", "applicant_age"],
    "income": ["income", "monthly_income", "annual_income", "salary"],
    "employment_status": ["employment_status", "job_status"],
    "education_level": ["education_level", "qualification"],
    "residence_type": ["residence_type", "urban_rural"],
    "social_category": ["social_category", "caste_category"],
    "gender": ["gender", "sex"],
    "disability_status": ["disability_status", "disabled"],
    "family_members": ["family_members", "dependents"]
}

# ============================================================
# HELPERS
# ============================================================

def normalize_columns(df):
    df.columns = df.columns.str.strip().str.lower()
    return df


def apply_aliases(df):
    for canonical, variants in COLUMN_ALIASES.items():
        for v in variants:
            v = v.lower()
            if v in df.columns and canonical not in df.columns:
                df.rename(columns={v: canonical}, inplace=True)
    return df


def prepare_features(df):
    for col in CANONICAL_FEATURES:
        if col not in df.columns:
            if col in ["age", "income", "family_members"]:
                df[col] = np.nan
            else:
                df[col] = "unknown"

    df["age"] = pd.to_numeric(df["age"], errors="coerce").fillna(df["age"].median())
    df["income"] = pd.to_numeric(df["income"], errors="coerce").fillna(df["income"].median())
    df["family_members"] = pd.to_numeric(df["family_members"], errors="coerce").fillna(0)

    for col in df.select_dtypes(include="object"):
        df[col] = df[col].fillna("unknown")

    return df


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(DATASET_PATH)
df = normalize_columns(df)
df = apply_aliases(df)
df = prepare_features(df)

X = df[CANONICAL_FEATURES]
y = df[TARGET_COLUMN]

# ============================================================
# FEATURE TYPES
# ============================================================

NUMERIC_COLS = ["age", "income", "family_members"]
CATEGORICAL_COLS = [c for c in CANONICAL_FEATURES if c not in NUMERIC_COLS]

preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_COLS),
        ("num", "passthrough", NUMERIC_COLS)
    ]
)

# ============================================================
# MODEL
# ============================================================

model = RandomForestClassifier(
    n_estimators=400,
    max_depth=16,
    min_samples_split=8,
    min_samples_leaf=4,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ]
)

# ============================================================
# TRAIN / TEST
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    stratify=y,
    random_state=42
)

pipeline.fit(X_train, y_train)

# ============================================================
# EVALUATION
# ============================================================

y_pred = pipeline.predict(X_test)

print("\nAccuracy:", round(accuracy_score(y_test, y_pred), 3))
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))

# ============================================================
# SAVE MODEL
# ============================================================

joblib.dump(pipeline, os.path.join(MODEL_DIR, r"C:\Users\saib4\Desktop\Policy scheme\models\government_policy_model.pkl"))
joblib.dump(CANONICAL_FEATURES, os.path.join(MODEL_DIR, r"C:\Users\saib4\Desktop\Policy scheme\models\required_features.pkl"))
joblib.dump(COLUMN_ALIASES, os.path.join(MODEL_DIR, r"C:\Users\saib4\Desktop\Policy scheme\models\column_aliases.pkl"))

print("\n✅ Government policy model trained & saved successfully")
