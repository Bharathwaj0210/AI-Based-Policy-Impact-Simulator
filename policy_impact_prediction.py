import pandas as pd
import joblib

# Load artifacts
model = joblib.load("policy_impact_model.pkl")
trained_features = joblib.load("trained_features.pkl")

def predict_from_csv(csv_path):
    df = pd.read_csv(csv_path)

    # Find common columns only
    common_features = [col for col in trained_features if col in df.columns]

    if len(common_features) == 0:
        raise ValueError("No common features found between trained model and uploaded dataset")

    X = df[common_features]

    predictions = model.predict(X)

    df["Predicted_Scheme"] = predictions
    return df
