# ============================================================
# GOVERNMENT POLICY DATASET REBUILDER (FINAL – INDUSTRY GRADE)
# ============================================================

import pandas as pd
import numpy as np

# ============================================================
# COLUMN ALIASES (CRITICAL)
# ============================================================

COLUMN_ALIASES = {
    "age": ["age", "age_years", "applicant_age"],
    "income": ["income", "monthly_income", "salary"],
    "gender": ["gender", "sex"],
    "state": ["state", "state_ut"],
    "education_level": ["education_level", "education"],
    "employment_status": ["employment_status", "employment"],
    "social_category": ["social_category", "caste"],
    "disability_status": ["disability_status", "disabled"],
    "scheme_name": ["scheme_name", "schemecategory", "scheme"],
    "min_age": ["min_age"],
    "max_age": ["max_age"],
    "income_limit": ["income_limit"],
    "gender_target": ["gender_target"]
}

# ============================================================
# CANONICAL FEATURES (TRAINING FEATURES)
# ============================================================

CANONICAL_FEATURES = [
    "age",
    "income",
    "gender",
    "education_level",
    "employment_status",
    "social_category",
    "disability_status",
    "scheme_name",
    "min_age",
    "max_age",
    "income_limit",
    "gender_target"
]

TARGET_COLUMN = "eligible"

# ============================================================
# UTIL FUNCTIONS
# ============================================================

def normalize_columns(df):
    df.columns = df.columns.str.strip().str.lower()
    return df


def apply_aliases(df):
    for canonical, variants in COLUMN_ALIASES.items():
        for v in variants:
            if v in df.columns and canonical not in df.columns:
                df.rename(columns={v: canonical}, inplace=True)
    return df


def ensure_columns(df):
    for col in CANONICAL_FEATURES:
        if col not in df.columns:
            if col in ["age", "income", "min_age", "max_age", "income_limit"]:
                df[col] = np.nan
            else:
                df[col] = "unknown"
    return df


def generate_eligibility(df):
    return (
        (df["age"] >= df["min_age"]) &
        (df["age"] <= df["max_age"]) &
        (df["income"] <= df["income_limit"]) &
        (
            (df["gender_target"] == "Any") |
            (df["gender"] == df["gender_target"])
        )
    ).astype(int)


# ============================================================
# MAIN PIPELINE
# ============================================================

def rebuild_dataset(input_csv, output_csv):
    df = pd.read_csv(input_csv)

    df = normalize_columns(df)
    df = apply_aliases(df)
    df = ensure_columns(df)

    # Convert numerics
    numeric_cols = ["age", "income", "min_age", "max_age", "income_limit"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median())

    # Generate eligibility target
    df[TARGET_COLUMN] = generate_eligibility(df)

    # Balance dataset
    eligible_df = df[df[TARGET_COLUMN] == 1]
    ineligible_df = df[df[TARGET_COLUMN] == 0].sample(
        n=len(eligible_df), random_state=42
    )

    final_df = pd.concat([eligible_df, ineligible_df]).sample(
        frac=1, random_state=42
    )

    final_df.to_csv(output_csv, index=False)

    print("✅ Government eligibility dataset created")
    print("Rows:", final_df.shape[0])
    print("Eligible %:", final_df[TARGET_COLUMN].mean())


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    rebuild_dataset(
        input_csv=r"C:\Users\saib4\Desktop\Policy scheme\enriched_gov_scheme_data.csv",
        output_csv="gov_eligibility_dataset.csv"
    )
