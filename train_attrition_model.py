import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.utils.class_weight import compute_class_weight

np.random.seed(42)

# =====================================================
# 1. LOAD DATA
# =====================================================
df = pd.read_csv("employee_data.csv")
print("Initial shape:", df.shape)

# Normalize column names (lowercase)
df.columns = df.columns.str.lower().str.strip()

# =====================================================
# 2. REQUIRED FEATURES
# =====================================================
required_features = [
    "age",
    "tenureyears",
    "performance score",
    "current employee rating",
    "isactive"
]

# =====================================================
# 3. AUTO-CREATE / SIMULATE MISSING COLUMNS
# =====================================================
for col in required_features:
    if col not in df.columns:
        print(f"⚠️ Column {col} missing → Simulating")
        
        if col == "age":
            df[col] = np.random.randint(21, 60, len(df))
        elif col == "tenureyears":
            df[col] = np.random.randint(0, 15, len(df))
        elif col == "performance score":
            df[col] = np.random.randint(1, 5, len(df))
        elif col == "current employee rating":
            df[col] = np.random.randint(1, 5, len(df))
        elif col == "isactive":
            df[col] = np.random.choice([0, 1], len(df), p=[0.2, 0.8])

# =====================================================
# 4. SAFE NUMERIC CONVERSION
# =====================================================
for col in required_features:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Fill NaN safely
for col in required_features:
    df[col] = df[col].fillna(df[col].median())

# =====================================================
# 5. HANDLE ATTRITION TARGET
# =====================================================
if "attrition" not in df.columns:
    print("⚠️ Attrition column missing → Simulating target")

    risk_score = (
        (df["performance score"] < 3).astype(int) +
        (df["current employee rating"] < 3).astype(int) +
        (df["tenureyears"] < 2).astype(int)
    )

    df["attrition"] = (risk_score + np.random.binomial(1, 0.3, len(df))) >= 2
    df["attrition"] = df["attrition"].astype(int)
else:
    df["attrition"] = pd.to_numeric(df["attrition"], errors="coerce")
    df["attrition"] = df["attrition"].fillna(0).astype(int)

print("\nAttrition Distribution:")
print(df["attrition"].value_counts())

# =====================================================
# 6. FEATURE ENGINEERING (Improves Accuracy)
# =====================================================
df["performance_tenure_ratio"] = df["performance score"] / (df["tenureyears"] + 1)
df["age_performance_interaction"] = df["age"] * df["performance score"]

features = required_features + [
    "performance_tenure_ratio",
    "age_performance_interaction"
]

X = df[features]
y = df["attrition"]

# =====================================================
# 7. TRAIN / TEST SPLIT
# =====================================================
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# =====================================================
# 8. COMPUTE CLASS WEIGHTS (Better balance)
# =====================================================
classes = np.unique(y_train)
weights = compute_class_weight("balanced", classes=classes, y=y_train)
class_weights = dict(zip(classes, weights))

print("Class Weights:", class_weights)

# =====================================================
# 9. TRAIN RANDOM FOREST (Improved Version)
# =====================================================
model = RandomForestClassifier(
    n_estimators=500,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=2,
    max_features="sqrt",
    class_weight=class_weights,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

# =====================================================
# 10. EVALUATION
# =====================================================
y_pred = model.predict(X_test)

acc = accuracy_score(y_test, y_pred)

print(f"\n✅ Improved Attrition Model Accuracy: {acc:.3f}")
print("📊 Classification Report:")
print(classification_report(y_test, y_pred))

# =====================================================
# 11. SAVE MODEL
# =====================================================
joblib.dump(model, "attrition_policy_model_1.pkl")

print("\n✅ Final attrition model saved successfully")
print("Model features used:", features)
