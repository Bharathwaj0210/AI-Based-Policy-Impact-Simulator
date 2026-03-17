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
        aliases_filename = "column_aliases.pkl"
        
        base_path = os.path.join(settings.BASE_DIR, "insurance", "models", insurance_type)
        if not os.path.exists(os.path.join(base_path, model_filename)):
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

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = df.columns.str.lower().str.strip()
        return df

    def safe_feature_subset(self, df, required_features):
        available = [c for c in required_features if c in df.columns]
        return df[available], available

    def predict(self, df):
        try:
            df = self.normalize(df)
            df = self.apply_aliases(df)
            X, used_features = self.safe_feature_subset(df, self.required_features)
            
            # Predict risk
            if hasattr(self.model, "predict_proba"):
                predictions = self.model.predict_proba(X)[:, 1].tolist()
            else:
                predictions = self.model.predict(X).tolist()
                
            return {
                "status": "success",
                "predictions": predictions,
                "used_features": used_features
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

def predict_insurance(data, insurance_type):
    service = InsurancePredictionService(insurance_type)
    return service.predict(data)
