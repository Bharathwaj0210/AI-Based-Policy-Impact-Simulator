import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# ===============================
# 1. LOAD DATA
# ===============================
df = pd.read_csv("employee_data.csv")
print("Initial shape:", df.shape)

# Standardize column names (lowercase for matching)
df.columns = df.columns.str.strip()

# ===============================
# 2. FLEXIBLE COLUMN MATCHING
# ===============================

REQUIRED_FEATURES = {
    "Age": ["age", "employee_age", "emp_age"],
    "TenureYears": ["tenure", "tenure_years", "experience", "years_at_company"],
    "Performance Score": ["performance", "performance_score", "perf_score"],
    "Current Employee Rating": ["rating", "employee_rating", "current_rating"],
    "IsActive": ["isactive", "active", "employment_status"]
}

created_columns = []

def find_column(possible_names):
    for col in df.columns:
        for name in possible_names:
            if name.lower() in col.lower():
                return col
    return None

# Create unified columns
for standard_name, variations in REQUIRED_FEATURES.items():
    found_col = find_column(variations)

    if found_col:
        df[standard_name] = df[found_col]
    else:
        # Simulate missing feature
        created_columns.append(standard_name)

        if standard_name == "Age":
            df[standard_name] = np.random.randint(20, 50, len(df))
        elif standard_name == "TenureYears":
            df[standard_name] = np.random.randint(0, 10, len(df))
        elif standard_name == "Performance Score":
            df[standard_name] = np.random.randint(1, 5, len(df))
        elif standard_name == "Current Employee Rating":
            df[standard_name] = np.random.randint(1, 5, len(df))
        elif standard_name == "IsActive":
            df[standard_name] = 1

# POP message for created columns
if created_columns:
    print("\n⚠️ The following required columns were missing and created automatically:")
    for col in created_columns:
        print("   ➜", col)
else:
    print("\n✅ All required features found in dataset.")

# ===============================
# 3. DATA CLEANING
# ===============================
for col in REQUIRED_FEATURES.keys():
    df[col] = pd.to_numeric(df[col], errors="coerce")
    df[col] = df[col].fillna(df[col].median())

df["IsActive"] = df["IsActive"].fillna(1).astype(int)

# ===============================
# 4. CREATE TARGET (Recruitment Selection)
# ===============================

np.random.seed(42)

df["Selected"] = (
    (df["Age"] >= 21).astype(int) +
    (df["Performance Score"] >= 3).astype(int) +
    (df["Current Employee Rating"] >= 3).astype(int)
)

# Add randomness to avoid leakage
df["Selected"] = (df["Selected"] + np.random.binomial(1, 0.3, len(df))) >= 2
df["Selected"] = df["Selected"].astype(int)

print("\nSelection distribution:")
print(df["Selected"].value_counts())

if df["Selected"].nunique() < 2:
    raise ValueError("❌ Selection label has only one class. Adjust rules.")

# ===============================
# 5. FEATURES
# ===============================
features = list(REQUIRED_FEATURES.keys())

X = df[features]
y = df["Selected"]

# ===============================
# 6. TRAIN TEST SPLIT
# ===============================
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# ===============================
# 7. TRAIN MODEL
# ===============================
model = RandomForestClassifier(
    n_estimators=300,
    max_depth=8,
    min_samples_leaf=10,
    random_state=42
)

model.fit(X_train, y_train)

# ===============================
# 8. EVALUATION
# ===============================
y_pred = model.predict(X_test)

print("\n✅ Recruitment Model Accuracy:", accuracy_score(y_test, y_pred))
print("📊 Classification Report:")
print(classification_report(y_test, y_pred))

# ===============================
# 9. SAVE MODEL
# ===============================
joblib.dump(model, "recruitment_policy_model_1.pkl")

print("\n✅ Recruitment model saved as recruitment_policy_model.pkl")
print("Model features used:", features)
