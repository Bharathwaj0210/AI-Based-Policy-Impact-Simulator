from core.utils import BasePredictionService
import pandas as pd

class HRPredictionService(BasePredictionService):
    def __init__(self, hr_type="attrition"):
        # hr/models contains models directly, no subdirs like insurance/models/<type>
        super().__init__(
            app_label="hr",
            model_dir_name="", # No subdir
            model_filename=f"{hr_type.lower().strip()}_policy_model.pkl",
            features_filename="model_features.pkl"
        )
    
    # Override align_features if specific HR logic is needed (e.g. median fill from streamlit)
    def align_features(self, df: pd.DataFrame):
        X, missing_features = super().align_features(df)
        # Based on streamlit: df_original[col].fillna(df_original[col].median())
        # The base service already does fillna(0), which is safe but we could refine if needed.
        return X, missing_features

def predict_hr(data, hr_type):
    service = HRPredictionService(hr_type)
    return service.predict(data)
