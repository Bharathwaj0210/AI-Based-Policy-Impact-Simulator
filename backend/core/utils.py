import os
import joblib
import pandas as pd
import numpy as np
from django.conf import settings
from abc import ABC, abstractmethod

class BasePredictionService(ABC):
    """
    Abstract Base Class for all Prediction Services.
    Ensures a consistent interface and provides common utilities.
    """

    def __init__(self, app_label, model_dir_name, model_filename, features_filename="required_features.pkl", aliases_filename=None):
        self.app_label = app_label
        self.model_dir_name = model_dir_name
        
        self.base_path = os.path.join(
            settings.BASE_DIR,
            app_label,
            "models",
            model_dir_name
        )

        self.model_path = os.path.join(self.base_path, model_filename)
        self.features_path = os.path.join(self.base_path, features_filename)
        self.aliases_path = os.path.join(self.base_path, aliases_filename) if aliases_filename else None

        self._validate_artifacts()
        self._load_artifacts()

    def _validate_artifacts(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        if not os.path.exists(self.features_path):
            raise FileNotFoundError(f"Features file not found: {self.features_path}")
        if self.aliases_path and not os.path.exists(self.aliases_path):
            # Optional, so we just log or ignore if missing
            pass

    def _load_artifacts(self):
        self.model = joblib.load(self.model_path)
        self.required_features = joblib.load(self.features_path)
        self.aliases = joblib.load(self.aliases_path) if self.aliases_path and os.path.exists(self.aliases_path) else {}

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = (
            df.columns
            .str.lower()
            .str.strip()
            .str.replace(" ", "_")
        )
        return df

    def apply_aliases(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for old, new in self.aliases.items():
            old = old.lower().strip()
            new = new.lower().strip()
            if old in df.columns and new not in df.columns:
                df.rename(columns={old: new}, inplace=True)
        return df

    def align_features(self, df: pd.DataFrame):
        df = df.copy()
        missing_features = []
        for col in self.required_features:
            if col not in df.columns:
                df[col] = np.nan
                missing_features.append(col)
        
        X = df[self.required_features]
        # Basic imputation if not handled by pipeline
        X = X.fillna(0) # Or X.fillna(X.median()) for more robustness if app-specific
        return X, missing_features

    def predict(self, data):
        try:
            if isinstance(data, dict):
                df = pd.DataFrame([data])
            elif isinstance(data, pd.DataFrame):
                df = data
            else:
                return {"status": "error", "message": "Unsupported data type"}

            if df.empty:
                return {"status": "error", "message": "Empty dataset provided"}

            df = self.normalize(df)
            df = self.apply_aliases(df)
            X, missing_features = self.align_features(df)

            if hasattr(self.model, "predict_proba"):
                predictions = self.model.predict_proba(X)[:, 1].tolist()
            else:
                predictions = self.model.predict(X).tolist()

            return {
                "status": "success",
                "type": self.model_dir_name,
                "predictions": predictions,
                "missing_features": missing_features,
                "used_features": list(X.columns),
                "total_records": len(X)
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
