import pandas as pd

# ===============================
# STEP 1: RULE ENGINE (GROUND TRUTH)
# ===============================
def check_eligibility(age, residence, occupation, pension, cooperative):
    if age < 18 or age > 60:
        return 0
    if residence != "Puducherry":
        return 0
    if occupation != "Fisherman":
        return 0
    if pension == "Yes":
        return 0
    if cooperative != "Yes":
        return 0
    return 1

# ===============================
# STEP 2: CREATE APPLICANTS (DIVERSE)
# ===============================
data = pd.DataFrame({
    "age": [25, 45, 62, 35, 55, 40, 30, 58],
    "residence": ["Puducherry", "Puducherry", "Puducherry", "Tamil Nadu",
                  "Puducherry", "Tamil Nadu", "Puducherry", "Puducherry"],
    "occupation": ["Fisherman", "Fisherman", "Fisherman", "Fisherman",
                   "Farmer", "Fisherman", "Farmer", "Fisherman"],
    "pension": ["No", "No", "No", "No", "No", "Yes", "No", "No"],
    "cooperative": ["Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "No"],
    "gender": ["Male", "Female", "Male", "Female", "Male", "Female", "Female", "Male"],
    "income_group": ["Low", "Low", "Low", "Medium", "Low", "Low", "High", "Low"]
})

# ===============================
# STEP 3: APPLY POLICY RULES
# ===============================
data["eligible"] = data.apply(
    lambda row: check_eligibility(
        row["age"],
        row["residence"],
        row["occupation"],
        row["pension"],
        row["cooperative"]
    ),
    axis=1
)

# ===============================
# STEP 4: FAIRNESS ANALYSIS
# ===============================
print("\n📊 Eligibility Rate by Gender")
print(data.groupby("gender")["eligible"].mean())

print("\n📊 Eligibility Rate by Income Group")
print(data.groupby("income_group")["eligible"].mean())

print("\n📊 Full Results")
print(data)
