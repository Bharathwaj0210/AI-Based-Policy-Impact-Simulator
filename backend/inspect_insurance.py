
import joblib
import os
import pandas as pd
import numpy as np

def inspect(domain):
    print(f"\n--- Inspecting {domain} ---")
    base = fr"c:\Users\bharathwaj\Desktop\AI POLICY (NEW)\backend\insurance\models\{domain}"
    model_path = os.path.join(base, "policy_rf_model.pkl")
    features_path = os.path.join(base, "required_features.pkl")
    aliases_path = os.path.join(base, "column_aliases.pkl")
    
    if os.path.exists(features_path):
        features = joblib.load(features_path)
        print(f"Required Features: {features}")
    
    if os.path.exists(aliases_path):
        aliases = joblib.load(aliases_path)
        print(f"Aliases: {aliases}")
        
    if os.path.exists(model_path):
        model = joblib.load(model_path)
        print(f"Model: {type(model)}")
        if hasattr(model, 'named_steps'):
            print(f"Steps: {list(model.named_steps.keys())}")

inspect("health")
inspect("vehicle")
