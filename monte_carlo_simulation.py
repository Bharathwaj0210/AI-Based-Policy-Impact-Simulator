import pandas as pd
import random

# ===============================
# ORIGINAL POLICY RULE
# ===============================
def original_policy(age, residence, occupation, pension, cooperative):
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
# RECOMMENDED POLICY RULE
# ===============================
def recommended_policy(age, residence, occupation, pension, cooperative):
    if age < 18 or age > 65:
        return 0
    if residence not in ["Puducherry", "Tamil Nadu"]:
        return 0
    if occupation not in ["Fisherman", "Fish Vendor", "Boat Worker"]:
        return 0
    if pension == "Yes":
        return 0
    return 1

# ===============================
# MONTE CARLO SIMULATION
# ===============================
def simulate(policy_function, n=1000):
    results = []

    for _ in range(n):
        age = random.randint(18, 70)
        residence = random.choice(["Puducherry", "Tamil Nadu", "Kerala"])
        occupation = random.choice(["Fisherman", "Farmer", "Fish Vendor", "Boat Worker"])
        pension = random.choice(["Yes", "No"])
        cooperative = random.choice(["Yes", "No"])

        eligible = policy_function(age, residence, occupation, pension, cooperative)
        results.append(eligible)

    return sum(results) / len(results)

# ===============================
# RUN MULTIPLE SIMULATIONS
# ===============================
original_results = []
recommended_results = []

for _ in range(50):  # 50 simulation runs
    original_results.append(simulate(original_policy))
    recommended_results.append(simulate(recommended_policy))

# ===============================
# RESULTS
# ===============================
print("\n📊 MONTE CARLO SIMULATION RESULTS")

print("\nOriginal Policy:")
print("Average Eligibility:", round(sum(original_results)/len(original_results), 3))
print("Best Case:", round(max(original_results), 3))
print("Worst Case:", round(min(original_results), 3))

print("\nRecommended Policy:")
print("Average Eligibility:", round(sum(recommended_results)/len(recommended_results), 3))
print("Best Case:", round(max(recommended_results), 3))
print("Worst Case:", round(min(recommended_results), 3))
