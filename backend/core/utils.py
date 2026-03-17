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
        self.original_features = joblib.load(self.features_path)
        # We still need normalized versions for alignment logic
        self.required_features = [f.lower().strip().replace(" ", "_") for f in self.original_features]
        # Create a mapping from normalized -> original
        self.feature_map = dict(zip(self.required_features, self.original_features))
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
                # If column is missing, we try to guess a safe default
                # This helps prevent Pipeline crashes
                df[col] = np.nan
                missing_features.append(col)
        
        X = df[self.required_features].copy()
        
        # Robustly handle types feature by feature
        for col in X.columns:
            # If already numeric, just fill
            if pd.api.types.is_numeric_dtype(X[col]):
                X[col] = X[col].fillna(0)
            else:
                # Try numeric conversion
                numeric_series = pd.to_numeric(X[col], errors='coerce')
                # If mostly numeric, keep as numeric
                if numeric_series.notna().sum() > (len(X[col]) / 2):
                    X[col] = numeric_series.fillna(0)
                else:
                    # Strictly categorical strings
                    # Ensure no np.nan remains; use apply(str) or map
                    X[col] = X[col].apply(lambda v: str(v) if pd.notna(v) and str(v).lower() != 'nan' else 'Unknown')
        
        # IMPORTANT: Rename back to original casing for scikit-learn exact match
        X = X.rename(columns=self.feature_map)
        
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
