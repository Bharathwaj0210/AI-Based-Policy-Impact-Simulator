import os
import pandas as pd
from django.conf import settings
from core.utils import BasePredictionService

class InsurancePredictionService(BasePredictionService):
    def __init__(self, insurance_type="health"):
        insurance_type = insurance_type.lower().strip()
        
        # Check for prefixed filenames or standard ones
        model_filename = "policy_rf_model.pkl"
        features_filename = "required_features.pkl"
        aliases_filename = "column_aliases.pkl" # Keep this line
        base_path = os.path.join(settings.BASE_DIR, "insurance", "models", insurance_type)
        
        # Custom behavior for new vehicle model filenames
        if insurance_type == "vehicle":
            if os.path.exists(os.path.join(base_path, "vehicle_claim_model.pkl")):
                model_filename = "vehicle_claim_model.pkl"
                features_filename = "vehicle_features.pkl"
                # Check for config
                self.config = {}
                config_path = os.path.join(base_path, "vehicle_model_config.pkl")
                if os.path.exists(config_path):
                    import joblib
                    self.config = joblib.load(config_path)
            
        elif not os.path.exists(os.path.join(base_path, model_filename)):
            model_filename = f"{insurance_type}_{model_filename}"
            features_filename = f"{insurance_type}_{features_filename}"
            aliases_filename = f"{insurance_type}_{aliases_filename}"
            
        super().__init__(
            app_label="insurance",
            model_dir_name=insurance_type,
            model_filename=model_filename,
            features_filename=features_filename,
            aliases_filename=aliases_filename
        )


    def preprocess_vehicle(self, df: pd.DataFrame) -> pd.DataFrame:
        """New feature engineering from training logic"""
        df = df.copy()
        REF_YEAR = 2020
        
        # Necessary Features (calculated from dates if available)
        if "date_birth" in df.columns:
            df["customer_age"] = REF_YEAR - pd.to_datetime(df["date_birth"], dayfirst=True, errors="coerce").dt.year
        if "date_driving_licence" in df.columns:
            df["driving_experience"] = REF_YEAR - pd.to_datetime(df["date_driving_licence"], dayfirst=True, errors="coerce").dt.year
        if "year_matriculation" in df.columns:
            df["vehicle_age"] = REF_YEAR - pd.to_numeric(df["year_matriculation"], errors="coerce")
            
        # Optional/Balance Features - Ensure they are numeric if they exist
        optional_features = ["value_vehicle", "cylinder_capacity", "premium", "power", "weight"]
        for feat in optional_features:
            if feat in df.columns:
                df[feat] = pd.to_numeric(df[feat], errors="coerce").fillna(0.0)
            
        # Fuel mapping (P=0, D=1)
        if "type_fuel" in df.columns:
            df["type_fuel"] = df["type_fuel"].map({"P": 0, "D": 1, "0": 0, "1": 1, "Gasoline": 0, "Diesel": 1}).fillna(0)
            
        # Common Categorical Mappings from Dataset Encoding
        if "area" in df.columns:
            df["area"] = df["area"].map({"Urban": 1, "Rural": 0, "1": 1, "0": 0, 1: 1, 0: 0}).fillna(0)
        if "payment" in df.columns:
            df["payment"] = df["payment"].map({"Monthly": 1, "Annual": 0, "1": 1, "0": 0, 1: 1, 0: 0}).fillna(0)
        if "type_risk" in df.columns:
            df["type_risk"] = df["type_risk"].map({"High": 1, "Low": 0, "1": 1, "0": 0, 1: 1, 0: 0}).fillna(0)
            
        return df

    def predict(self, df):
        df = self.normalize(df)
        df = self.apply_aliases(df)
        
        # Application-specific preprocessing
        if self.model_dir_name == "vehicle":
            df = self.preprocess_vehicle(df)
            
        X, used_features = self.align_features(df)
        
        # Predict risk
        if hasattr(self.model, "predict_proba"):
            predictions = self.model.predict_proba(X)[:, 1].tolist()
        else:
            predictions = self.model.predict(X).tolist()
            
        return {
            "status": "success",
            "predictions": predictions,
            "used_features": used_features,
            "config": getattr(self, "config", {})
        }

def predict_insurance(data, insurance_type):
    service = InsurancePredictionService(insurance_type)
    return service.predict(data)
