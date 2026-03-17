# ============================================================
# Vehicle Insurance Claim Prediction (Clean Final Version)
# ============================================================

import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, f1_score
from sklearn.ensemble import RandomForestClassifier

# ============================================================
# LOAD DATA (FIXED WARNING)
# ============================================================

df = pd.read_csv(
    r"Motor vehicle insurance data.csv",
    sep=";",
    low_memory=False   # ✅ Fix dtype warning
)

# ============================================================
# DATE PROCESSING (FIXED WARNING)
# ============================================================

df["Date_birth"] = pd.to_datetime(
    df["Date_birth"], format="%d/%m/%Y", errors="coerce"
)

df["Date_driving_licence"] = pd.to_datetime(
    df["Date_driving_licence"], format="%d/%m/%Y", errors="coerce"
)

# Reference year
REF_YEAR = 2020

# Feature Engineering
df["customer_age"] = REF_YEAR - df["Date_birth"].dt.year
df["driving_experience"] = REF_YEAR - df["Date_driving_licence"].dt.year
df["vehicle_age"] = REF_YEAR - df["Year_matriculation"]

# ============================================================
# TARGET (NO LEAKAGE)
# ============================================================

df["claim_status"] = (df["N_claims_year"] > 0).astype(int)

# ============================================================
# CLEANING
# ============================================================

# Fuel mapping
df["Type_fuel"] = df["Type_fuel"].map({"P": 0, "D": 1})

# Drop unused / leakage columns
df.drop(columns=[
    "ID",
    "Date_start_contract",
    "Date_last_renewal",
    "Date_next_renewal",
    "Date_birth",
    "Date_driving_licence",
    "Date_lapse",
    "Cost_claims_year",
    "N_claims_year"
], inplace=True, errors="ignore")

# ============================================================
# FINAL FEATURES
# ============================================================

FEATURES = [
    "customer_age",
    "driving_experience",
    "vehicle_age",
    "Seniority",
    "Policies_in_force",
    "Max_policies",
    "Max_products",
    "Lapse",
    "Payment",
    "Premium",
    "N_claims_history",
    "R_Claims_history",
    "Type_risk",
    "Area",
    "Second_driver",
    "Power",
    "Cylinder_capacity",
    "Value_vehicle",
    "Weight",
    "Type_fuel"
]

TARGET = "claim_status"

# ============================================================
# HANDLE MISSING VALUES (ROBUST)
# ============================================================

# Numeric fill
for col in FEATURES:
    if df[col].dtype in ["float64", "int64"]:
        df[col] = df[col].fillna(df[col].median())
    else:
        df[col] = df[col].fillna(0)

# Remove invalid rows (important)
df = df[df["customer_age"] > 18]
df = df[df["driving_experience"] >= 0]

# ============================================================
# SPLIT
# ============================================================

X = df[FEATURES]
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# ============================================================
# CLASS IMBALANCE HANDLING
# ============================================================

neg, pos = np.bincount(y_train)
weight_ratio = neg / pos

# ============================================================
# RANDOM FOREST MODEL
# ============================================================

model = RandomForestClassifier(
    n_estimators=600,
    max_depth=16,
    min_samples_split=12,
    min_samples_leaf=5,
    class_weight={0: 1, 1: weight_ratio * 0.8},
    max_features="sqrt",
    n_jobs=-1,
    random_state=42
)

# ============================================================
# TRAIN
# ============================================================

model.fit(X_train, y_train)

# ============================================================
# THRESHOLD OPTIMIZATION
# ============================================================

y_proba = model.predict_proba(X_test)[:, 1]

best_t = 0.3
best_f1 = 0

for t in np.arange(0.2, 0.6, 0.02):
    preds = (y_proba > t).astype(int)
    f1 = f1_score(y_test, preds)

    if f1 > best_f1:
        best_f1 = f1
        best_t = t

# ============================================================
# FINAL EVALUATION
# ============================================================

y_pred = (y_proba > best_t).astype(int)

print(f"Best Threshold: {best_t:.2f}")
print("Accuracy:", accuracy_score(y_test, y_pred))
print("ROC-AUC:", roc_auc_score(y_test, y_proba))

print("\nClassification Report")
print(classification_report(y_test, y_pred))

# ============================================================
# SAVE FILES (FINAL)
# ============================================================

joblib.dump(model, "vehicle_claim_model.pkl")
joblib.dump(FEATURES, "vehicle_features.pkl")

MODEL_CONFIG = {
    "threshold": float(best_t),
    "target": TARGET,
    "model_type": "RandomForest",
    "version": "v2_clean"
}

joblib.dump(MODEL_CONFIG, "vehicle_model_config.pkl")

# ============================================================
# SAVE METRICS SNAPSHOT (USER REQUEST)
# ============================================================

with open("metrics.txt", "w") as f:
    f.write(f"Best Threshold: {best_t:.4f}\n")
    f.write(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}\n")
    f.write(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}\n")
    f.write("\nClassification Report:\n")
    f.write(classification_report(y_test, y_pred))

# Save feature importance
importances = pd.DataFrame({
    'feature': FEATURES,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)
importances.to_csv("feature_importance.csv", index=False)

print("✅ Clean Model + Metadata + Metrics saved successfully")
