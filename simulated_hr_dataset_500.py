import pandas as pd
import numpy as np

np.random.seed(42)

rows = 500

df = pd.DataFrame({
    "Age": np.random.randint(20, 61, rows),
    "TenureYears": np.round(np.random.uniform(0, 15, rows), 1),
    "Performance Score": np.random.randint(1, 6, rows),
    "Current Employee Rating": np.random.randint(1, 6, rows),
    "IsActive": np.random.choice([0, 1], rows, p=[0.15, 0.85]),

    "Gender": np.random.choice(["Male", "Female"], rows),
    "Department": np.random.choice(
        ["Sales", "IT", "HR", "Finance", "Operations"], rows
    ),
    "JobLevel": np.random.randint(1, 6, rows),
    "MonthlyIncome": np.random.randint(20000, 120001, rows),
    "WorkLifeBalance": np.random.randint(1, 5, rows),
    "JobSatisfaction": np.random.randint(1, 5, rows),
    "TrainingHours": np.random.randint(0, 81, rows),
    "PromotionLast5Years": np.random.choice([0, 1], rows, p=[0.7, 0.3]),
    "Attrition": np.random.choice([0, 1], rows, p=[0.8, 0.2])
})

# Save dataset
df.to_csv("simulated_hr_dataset_500.csv", index=False)

print("✅ Dataset generated: simulated_hr_dataset_500.csv")
print(df.head())
