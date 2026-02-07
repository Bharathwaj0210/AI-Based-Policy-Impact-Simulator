import pandas as pd

# ===============================
# STEP 1: LOAD DATASET
# ===============================
df = pd.read_csv("updated_data.csv", encoding="utf-8")

# ===============================
# STEP 2: CLEAN CURRENCY & SYMBOLS
# ===============================
def clean_text(text):
    if isinstance(text, str):
        text = text.replace("â‚¹", "₹")
        text = text.replace("ï»¿", "")
        text = text.replace("â€™", "'")
        text = text.replace("â€“", "-")
        text = text.replace("â€œ", '"').replace("â€�", '"')
    return text

df = df.applymap(clean_text)

print("✅ Symbols and currency cleaned")

# ===============================
# STEP 3: ADD ELIGIBILITY RULE COLUMNS
# ===============================
df["min_age"] = 18
df["max_age"] = 60
df["residency_required"] = "Puducherry"
df["occupation_required"] = "Fisherman"
df["pension_allowed"] = "No"
df["cooperative_member"] = "Yes"

print("✅ Rule-based eligibility columns added")

# ===============================
# STEP 4: POLICY RULE ENGINE
# ===============================
def check_eligibility(age, residence, occupation, pension):
    if age < 18 or age > 60:
        return "Rejected: Age Rule"
    if residence != "Puducherry":
        return "Rejected: Residency Rule"
    if occupation != "Fisherman":
        return "Rejected: Occupation Rule"
    if pension == "Yes":
        return "Rejected: Pension Rule"
    return "Eligible"

# ===============================
# STEP 5: SIMULATE FAKE APPLICANTS
# ===============================
applicants = pd.DataFrame({
    "age": [45, 62, 30, 55],
    "residence": ["Puducherry", "Puducherry", "Tamil Nadu", "Puducherry"],
    "occupation": ["Fisherman", "Fisherman", "Fisherman", "Farmer"],
    "pension": ["No", "No", "No", "No"],
    "gender": ["Male", "Male", "Female", "Female"],
    "income_group": ["Low", "Low", "Medium", "Low"]
})

applicants["eligibility_result"] = applicants.apply(
    lambda row: check_eligibility(
        row["age"],
        row["residence"],
        row["occupation"],
        row["pension"]
    ),
    axis=1
)

print("\n=== SIMULATION RESULTS ===")
print(applicants)

# ===============================
# STEP 6: BASIC FAIRNESS ANALYSIS
# ===============================
fairness = applicants.groupby("gender")["eligibility_result"].value_counts()
print("\n=== FAIRNESS ANALYSIS (BY GENDER) ===")
print(fairness)

# ===============================
# STEP 7: SAVE FINAL DATASET
# ===============================
df.to_csv("cleaned_policy_dataset.csv", index=False)
applicants.to_csv("simulated_applicants_results.csv", index=False)

print("\n🎉 ALL DONE")
print("✔ cleaned_policy_dataset.csv saved")
print("✔ simulated_applicants_results.csv saved")
