
import pandas as pd
import numpy as np
import os

def generate_health_data(path, n=100):
    data = {
        'age': np.random.randint(18, 80, n),
        'sex': np.random.choice(['male', 'female'], n),
        'bmi': np.round(np.random.uniform(18.0, 45.0, n), 1),
        'children': np.random.randint(0, 5, n),
        'smoker': np.random.choice(['yes', 'no'], n),
        'region': np.random.choice(['southwest', 'southeast', 'northwest', 'northeast'], n)
    }
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Generated health data: {path}")

def generate_vehicle_data(path, n=100):
    data = {
        'vehicle_age': np.random.randint(0, 20, n),
        'vehicle_type': np.random.choice(['Sedan', 'SUV', 'Hatchback', 'Truck'], n),
        'engine_capacity': np.random.choice([1000, 1500, 2000, 2500, 3000], n),
        'fuel_type': np.random.choice(['Petrol', 'Diesel', 'Electric', 'Hybrid'], n),
        'vehicle_value': np.random.randint(5000, 80000, n),
        'owner_age': np.random.randint(18, 80, n),
        'owner_gender': np.random.choice(['Male', 'Female'], n),
        'driving_experience_years': np.random.randint(0, 50, n),
        'accident_history': np.random.randint(0, 10, n),
        'annual_mileage': np.random.randint(2000, 30000, n),
        'claim_frequency': np.random.randint(0, 5, n),
        'no_claim_bonus': np.random.randint(0, 60, n),
        'policy_type': np.random.choice(['Third Party', 'Comprehensive'], n),
        'urban_vs_rural': np.random.choice(['Urban', 'Rural'], n)
    }
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Generated vehicle data: {path}")

# Paths
health_path = r"c:\Users\bharathwaj\Desktop\AI POLICY (NEW)\backend\insurance\test_data\health\test_health_100.csv"
vehicle_path = r"c:\Users\bharathwaj\Desktop\AI POLICY (NEW)\backend\insurance\test_data\vehicle\test_vehicle_100.csv"

generate_health_data(health_path)
generate_vehicle_data(vehicle_path)
