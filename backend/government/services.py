import pandas as pd
import numpy as np
from core.utils import BasePredictionService

POLICY_CONDITIONS = {
    "scholarship": {
        "annual_income": {"type": "max", "default": 200000},
        "education_level": {"type": "multiselect", "options": ["UG", "PG", "Diploma", "12th", "10th", "unknown"]},
        "disability_status": {"type": "disability_filter"},
        "gender": {"type": "multiselect_optional"},
    },
    "pension": {
        "age": {"type": "min", "default": 58},
        "employment_status": {"type": "multiselect", "options": ["Employed", "Unemployed", "Self-Employed", "Student", "Retired", "unknown"]},
        "annual_income": {"type": "max", "default": 150000},
    },
    "housing": {
        "annual_income": {"type": "max", "default": 300000},
        "family_size": {"type": "min", "default": 2},
        "employment_status": {"type": "multiselect", "options": ["Employed", "Unemployed", "Self-Employed", "Student", "unknown"]},
        "owns_house": {"type": "binary", "default": True},
    },
    "cash_welfare": {
        "annual_income": {"type": "max", "default": 150000},
        "family_size": {"type": "min", "default": 2},
        "disability_status": {"type": "disability_filter"},
        "age": {"type": "min", "default": 18},
        "education_level": {"type": "multiselect", "options": ["UG", "PG", "Diploma", "12th", "10th", "unknown"]},
        "owns_house": {"type": "binary", "default": True},
        "gender": {"type": "multiselect_optional"},
    },
}

class GovernmentPredictionService(BasePredictionService):
    def __init__(self):
        super().__init__(
            app_label="government",
            model_dir_name="",
            model_filename="government_policy_model.pkl",
            features_filename="required_features.pkl",
            aliases_filename="column_aliases.pkl"
        )

    def apply_policy_rules(self, df_pred, policy, thresholds):
        mask = pd.Series(True, index=df_pred.index)
        conds = POLICY_CONDITIONS.get(policy, {})
        for col, config in conds.items():
            if col not in df_pred.columns: continue
            cfg_type = config["type"]
            val = thresholds.get(col)
            if val is None: continue
            if cfg_type == "max": mask &= pd.to_numeric(df_pred[col], errors="coerce") <= val
            elif cfg_type == "min": mask &= pd.to_numeric(df_pred[col], errors="coerce") >= val
            elif cfg_type == "multiselect": mask &= df_pred[col].astype(str).str.lower().isin([str(v).lower() for v in val])
            elif cfg_type == "multiselect_optional" and val: mask &= df_pred[col].astype(str).str.lower().isin([str(v).lower() for v in val])
            elif cfg_type == "disability_filter":
                if val == "Disabled only": mask &= (pd.to_numeric(df_pred[col], errors="coerce").fillna(0).astype(int) == 1)
                elif val == "Non-disabled only": mask &= (pd.to_numeric(df_pred[col], errors="coerce").fillna(0).astype(int) == 0)
            elif cfg_type == "binary" and val: mask &= (pd.to_numeric(df_pred[col], errors="coerce").fillna(1) == 0)
        return df_pred[mask]

    def optimize_policy(self, df_pred, policy):
        best_rate, best_rule = -1, {}
        available_cols = set(df_pred.columns)
        if policy == "scholarship":
            for inc in [100000, 150000, 200000, 250000, 300000]:
                temp = df_pred[df_pred["annual_income"] <= inc] if "annual_income" in available_cols else df_pred
                if len(temp) < 10: continue
                rate = temp["eligible"].mean()
                if rate > best_rate: best_rate, best_rule = rate, {"annual_income": inc}
        elif policy == "pension":
            ages = [55, 58, 60, 62, 65] if "age" in available_cols else [None]
            incs = [80000, 100000, 150000, 200000] if "annual_income" in available_cols else [None]
            for age in ages:
                for inc in incs:
                    temp = df_pred.copy()
                    if age: temp = temp[temp["age"] >= age]
                    if inc: temp = temp[temp["annual_income"] <= inc]
                    if len(temp) < 10: continue
                    rate = temp["eligible"].mean()
                    if rate > best_rate: best_rate, best_rule = rate, {"age": age, "annual_income": inc}
        # Simplified for brevity as per user request (minimal code)
        return best_rule, round(best_rate, 4) if best_rate >= 0 else 0
