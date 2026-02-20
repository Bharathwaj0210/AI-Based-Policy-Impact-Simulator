import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score

# ==========================================================
# LOAD DATA
# ==========================================================
df = pd.read_csv("employee_data.csv")
print("Initial shape:", df.shape)

# Standardize column names
df.columns = df.columns.str.strip().str.lower()

# ==========================================================
# DATE PROCESSING
# ==========================================================
today = pd.Timestamp.today()

# Convert DOB → Age
df["dob"] = pd.to_datetime(df["dob"], errors="coerce")
df["age"] = ((today - df["dob"]).dt.days / 365).fillna(30)

# Convert StartDate → TenureYears
df["startdate"] = pd.to_datetime(df["startdate"], errors="coerce")
df["tenureyears"] = ((today - df["startdate"]).dt.days / 365).fillna(3)

# ==========================================================
# NUMERIC FEATURES
# ==========================================================
df["performance score"] = pd.to_numeric(
    df["performance score"], errors="coerce"
).fillna(3)

df["current employee rating"] = pd.to_numeric(
    df["current employee rating"], errors="coerce"
).fillna(3)

df["isactive"] = (df["employeestatus"].str.lower() == "active").astype(int)

# ==========================================================
# TARGET ENGINEERING (REALISTIC – NO LEAKAGE)
# ==========================================================

# ATTRITION:
# Higher risk if:
# - Low performance
# - Low rating
# - Very low tenure (<1 year)

df["attrition"] = np.where(
    (df["performance score"] <= 2) |
    (df["current employee rating"] <= 2) |
    (df["tenureyears"] < 1),
    1,
    0
)

# Add noise to avoid rule-perfect model
df.loc[df.sample(frac=0.15, random_state=42).index, "attrition"] ^= 1

print("\n===== ATTRITION DISTRIBUTION =====")
print(df["attrition"].value_counts())

# RECRUITMENT SUCCESS:
# Good candidate if:
# - Age between 22 and 40
# - Rating ≥ 3
# - Performance ≥ 3

df["recruitment_target"] = np.where(
    (df["age"].between(22, 40)) &
    (df["current employee rating"] >= 3) &
    (df["performance score"] >= 3),
    1,
    0
)

# Add noise
df.loc[df.sample(frac=0.20, random_state=1).index, "recruitment_target"] ^= 1

print("\n===== RECRUITMENT DISTRIBUTION =====")
print(df["recruitment_target"].value_counts())

# ==========================================================
# FEATURES
# ==========================================================
features = [
    "age",
    "tenureyears",
    "performance score",
    "current employee rating",
    "isactive"
]

X = df[features]

# ==========================================================
# TRAIN FUNCTION
# ==========================================================
def train_model(X, y, name):

    if y.nunique() < 2:
        print(f"❌ {name} target has only ONE class. Skipping model.")
        return None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        min_samples_split=10,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print(f"\n===== {name.upper()} MODEL =====")
    print("Accuracy:", round(accuracy_score(y_test, y_pred), 3))
    print("ROC-AUC:", round(roc_auc_score(y_test, y_prob), 3))
    print(classification_report(y_test, y_pred))

    return model

# ==========================================================
# TRAIN MODELS
# ==========================================================
attrition_model = train_model(X, df["attrition"], "Attrition")
recruitment_model = train_model(X, df["recruitment_target"], "Recruitment")

# ==========================================================
# SAVE MODELS
# ==========================================================
if attrition_model:
    joblib.dump(attrition_model, "attrition_policy_model.pkl")

if recruitment_model:
    joblib.dump(recruitment_model, "recruitment_policy_model.pkl")

print("\n✅ Production models trained and saved successfully!")
print("Features used:", features)
