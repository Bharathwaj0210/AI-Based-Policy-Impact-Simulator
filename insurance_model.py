# ============================================================
# AI-Based Policy Impact Simulator
# Full Training Code (Single File, No Splits)
# Algorithm: Random Forest
# ============================================================

import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score
)

from sklearn.ensemble import RandomForestClassifier

# ============================================================
# CONFIGURATION
# ============================================================

CANONICAL_FEATURES = [
    "age",
    "sex",
    "bmi",
    "smoker",
    "income",
    "pre_existing_conditions",
    "hospital_visits_last_year",
    "claim_frequency",
    "location_risk_score"
]

TARGET_COLUMN = "policy_approved"

COLUMN_ALIASES = {
    "customer_age": "age",
    "insured_age": "age",
    "age_years": "age",

    "gender": "sex",
    "gender_identity": "sex",

    "body_mass_index": "bmi",
    "bmi_value": "bmi",

    "smoking_status": "smoker",
    "is_smoker": "smoker",
    "smokes": "smoker",

    "annual_income": "income",
    "monthly_income": "income",
    "salary": "income",

    "existing_conditions": "pre_existing_conditions",
    "chronic_conditions": "pre_existing_conditions",

    "hospital_visits": "hospital_visits_last_year",
    "hospital_visits_past_year": "hospital_visits_last_year",

    "num_claims": "claim_frequency",

    "geo_risk_score": "location_risk_score",

    "approval_status": "policy_approved",
    "is_policy_approved": "policy_approved"
}

# ============================================================
# UTIL FUNCTIONS
# ============================================================

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for old_col, new_col in COLUMN_ALIASES.items():
        if old_col in df.columns and new_col not in df.columns:
            df.rename(columns={old_col: new_col}, inplace=True)
    return df


def validate_required_features(df: pd.DataFrame):
    missing = [c for c in CANONICAL_FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Training blocked. Missing columns: {missing}")

# ============================================================
# LOAD DATASET
# ============================================================

df = pd.read_csv(r"C:\Users\bharathwaj\Desktop\Mini-Project\Data.csv")
df = normalize_columns(df)
validate_required_features(df)

X = df[CANONICAL_FEATURES]
y = df[TARGET_COLUMN]

# ============================================================
# FEATURE TYPES
# ============================================================

categorical_features = ["sex", "smoker"]

numerical_features = [
    "age",
    "bmi",
    "income",
    "pre_existing_conditions",
    "hospital_visits_last_year",
    "claim_frequency",
    "location_risk_score"
]

# ============================================================
# PREPROCESSOR
# ============================================================

preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
        ("num", "passthrough", numerical_features)
    ]
)

# ============================================================
# RANDOM FOREST MODEL
# ============================================================

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    min_samples_split=10,
    min_samples_leaf=5,
    max_features="sqrt",
    class_weight="balanced",
    n_jobs=-1,
    random_state=42
)

pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ]
)

# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    stratify=y,
    random_state=42
)

# ============================================================
# TRAIN MODEL
# ============================================================

pipeline.fit(X_train, y_train)

# ============================================================
# EVALUATION
# ============================================================

y_pred = pipeline.predict(X_test)
y_proba = pipeline.predict_proba(X_test)[:, 1]

accuracy = accuracy_score(y_test, y_pred)
roc_auc = roc_auc_score(y_test, y_proba)

print(f"Model Accuracy: {accuracy:.4f}")
print(f"ROC-AUC Score: {roc_auc:.4f}")

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred, digits=4))

# ============================================================
# SAVE MODEL + METADATA
# ============================================================

joblib.dump(pipeline, "policy_rf_model.pkl")
joblib.dump(CANONICAL_FEATURES, "required_features.pkl")
joblib.dump(COLUMN_ALIASES, "column_aliases.pkl")

print("Training completed. Model and schema saved successfully.")
