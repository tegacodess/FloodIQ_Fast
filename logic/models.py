import os
import joblib
import pandas as pd

class FloodModelManager:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = self._load_artifact()
        # Enforce exact column order corresponding to model training arrays
        self.feature_columns = [
            'swvl1', 'tp_mm', 'runoff_mm', 'temp_c', 
            'elevation', 'slope', 'flow_accum', 
            'is_rainy_season', 'rolling_3day_feat', 'rolling_5day_feat'
        ]

    def _load_artifact(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Critical ML Artifact missing at: {self.model_path}")
        return joblib.load(self.model_path)

    def evaluate_risk(self, feature_df: pd.DataFrame) -> tuple[int, float, str]:
        """Runs inference and handles threshold mapping logic."""
        # Align column layout perfectly to isolate against unexpected schemas
        X = feature_df[self.feature_columns]
        
        # Calculate Class Probabilities [Class 0, Class 1]
        probabilities = self.model.predict_proba(X)[0]
        flood_probability = float(probabilities[1])
        prediction_class = int(self.model.predict(X)[0])
        
        # Determine actionable risk alert configurations
        if flood_probability > 0.70:
            risk_level = "HIGH"
        elif flood_probability > 0.40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        return prediction_class, flood_probability, risk_level