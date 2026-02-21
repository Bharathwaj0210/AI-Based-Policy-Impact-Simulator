import os
from django.conf import settings
from core.utils import BasePredictionService

class InsurancePredictionService(BasePredictionService):
    def __init__(self, insurance_type="health"):
        insurance_type = insurance_type.lower().strip()
        
        # Check for prefixed filenames or standard ones
        model_filename = "policy_rf_model.pkl"
        features_filename = "required_features.pkl"
        aliases_filename = "column_aliases.pkl"
        
        # In some folders (like vehicle), files are prefixed with the type
        # We'll check if the standard one exists, if not we assume prefixed
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

def predict_insurance(data, insurance_type):
    service = InsurancePredictionService(insurance_type)
    return service.predict(data)
