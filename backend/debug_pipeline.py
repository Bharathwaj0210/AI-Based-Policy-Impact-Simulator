
import joblib
import pandas as pd
import numpy as np

def debug_pipeline(domain):
    print(f"\n--- Debugging Pipeline: {domain} ---")
    base = fr"c:\Users\bharathwaj\Desktop\AI POLICY (NEW)\backend\insurance\models\{domain}"
    model_path = os.path.join(base, "policy_rf_model.pkl")
    
    pipeline = joblib.load(model_path)
    if not hasattr(pipeline, 'named_steps'):
        print("Not a pipeline")
        return
        
    preprocessor = pipeline.named_steps.get('preprocessor')
    if preprocessor:
        print(f"Preprocessor: {preprocessor}")
        try:
            # Inspection of ColumnTransformer
            for name, transformer, columns in preprocessor.transformers_:
                print(f"Step: {name}, Transformer: {transformer}, Columns: {columns}")
        except:
            print("Could not inspect transformers (maybe not fitted or different version)")
    
import os
debug_pipeline("health")
debug_pipeline("vehicle")
