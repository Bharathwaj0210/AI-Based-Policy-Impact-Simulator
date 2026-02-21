from pathlib import Path

# Base directory of backend
BASE_DIR = Path(__file__).resolve().parent.parent

# Model directories
MODEL_DIR = BASE_DIR / "insurance" / "models"

HEALTH_MODEL_DIR = MODEL_DIR / "health"
VEHICLE_MODEL_DIR = MODEL_DIR / "vehicle"

GOVERNMENT_MODEL_DIR = BASE_DIR / "government" / "models"

# Model filenames
MODEL_FILE = "policy_rf_model.pkl"
FEATURES_FILE = "required_features.pkl"
ALIASES_FILE = "column_aliases.pkl"

# Supported policy types
SUPPORTED_POLICIES = ["health", "vehicle", "government"]

# Prediction status
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
STATUS_WARNING = "warning"
