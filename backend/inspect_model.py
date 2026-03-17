
import joblib
import os

model_path = r"c:\Users\bharathwaj\Desktop\AI POLICY (NEW)\backend\insurance\models\health\policy_rf_model.pkl"
features_path = r"c:\Users\bharathwaj\Desktop\AI POLICY (NEW)\backend\insurance\models\health\required_features.pkl"
aliases_path = r"c:\Users\bharathwaj\Desktop\AI POLICY (NEW)\backend\insurance\models\health\column_aliases.pkl"

try:
    features = joblib.load(features_path)
    print(f"Required Features: {features}")
    
    if os.path.exists(aliases_path):
        aliases = joblib.load(aliases_path)
        print(f"Column Aliases: {aliases}")
    
    model = joblib.load(model_path)
    print(f"Model Type: {type(model)}")
    if hasattr(model, 'named_steps'):
        print(f"Pipeline Steps: {list(model.named_steps.keys())}")
        if 'preprocessor' in model.named_steps:
            print(f"Preprocessor: {model.named_steps['preprocessor']}")
except Exception as e:
    print(f"Error: {e}")
