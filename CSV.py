import pandas as pd
import numpy as np

np.random.seed(42)
rows = 100

data = {
    "age": np.random.randint(18, 80, size=rows),
    "sex": np.random.choice(["male", "female"], size=rows),
    "bmi": np.round(np.random.uniform(18, 50, size=rows), 1),
    "children": np.random.randint(0, 5, size=rows),
    "smoker": np.random.choice(["yes", "no"], size=rows, p=[0.2, 0.8]),
    "region": np.random.choice(["southeast", "southwest", "northeast", "northwest"], size=rows),
    "income": np.random.randint(30000, 150000, size=rows),
    "education": np.random.choice(["High School", "Bachelor", "Master", "PhD"], size=rows),
    "employment_status": np.random.choice(["Employed", "Unemployed", "Retired", "Self-Employed"], size=rows),
    "pre_existing_conditions": np.random.randint(0, 5, size=rows),
    "exercise_frequency": np.random.choice(["Rarely", "Moderate", "Active"], size=rows),
    "occupation_risk": np.round(np.random.uniform(0.1, 1.0, size=rows), 2),
    "hospital_visits_last_year": np.random.randint(0, 10, size=rows),
    "blood_pressure": np.random.randint(110, 180, size=rows),
    "cholesterol_level": np.random.randint(150, 300, size=rows),
    "daily_steps": np.random.randint(2000, 15000, size=rows),
    "alcohol_consumption": np.random.choice(["Low", "Medium", "High"], size=rows),
    "years_as_customer": np.random.randint(0, 20, size=rows),
    "policy_type": np.random.choice(["Basic", "Silver", "Gold"], size=rows),
    "urban_vs_rural": np.random.choice(["Urban", "Rural"], size=rows),
    "genetic_risk_score": np.round(np.random.uniform(0, 1, size=rows), 3),
    "marital_status": np.random.choice(["Single", "Married", "Divorced", "Widowed"], size=rows),
    "claim_frequency": np.random.randint(0, 5, size=rows),
    "location_risk_score": np.round(np.random.uniform(0, 1, size=rows), 3),
    "charges": np.round(np.random.uniform(5000, 80000, size=rows), 2)
}

df = pd.DataFrame(data)
df.to_csv("synthetic_insurance_data.csv", index=False)
print("Synthetic dataset generated: synthetic_insurance_data.csv")
