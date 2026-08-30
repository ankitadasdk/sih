import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

JUDICIAL_OUTCOMES = {
    0: "Bail Granted (Regular / Default Bail)",
    1: "Remanded to Judicial Custody (Bail Rejected)",
    2: "Interim Relief / Conditional Bail"
}

FEATURE_COLS = [
    "custody_duration_days",
    "charge_sheet_filed",
    "account_frozen_indicator",
    "statutory_cert_present",
    "heinous_offense_flag",
    "prior_antecedents_count",
    "flight_risk_indicator",
    "unauthorized_amount_inr",
    "recovery_effected_ratio"
]


class JudicialReliefPredictor:
    def __init__(self, model_path: str = "models/judicial_predictor.pkl"):
        self.model_path = model_path
        self.pipeline = None
        self.features = FEATURE_COLS
        self.outcome_mapping = JUDICIAL_OUTCOMES
        self._ensure_model_ready()

    # ==========================================
    # 1. SYNTHETIC DATASET GENERATION & TRAINING
    # ==========================================
    def _generate_synthetic_judicial_data(self, n_samples: int = 10000) -> pd.DataFrame:
        """
        Synthesizes judicial parameters based on statutory CrPC / BNSS bail milestones:
        - Default bail triggers if chargesheet not filed within 60/90 days.
        - Section 63 BSA / 65B certification impact on prime facie evidence strength.
        - Asset freezing and recovery ratio influence on financial fraud relief.
        """
        np.random.seed(42)
        records = []

        for _ in range(n_samples):
            custody_days = np.random.randint(1, 180)
            charge_sheet_filed = int(np.random.choice([0, 1], p=[0.45, 0.55]))
            account_frozen = int(np.random.choice([0, 1], p=[0.40, 0.60]))
            statutory_cert = int(np.random.choice([0, 1], p=[0.35, 0.65]))
            heinous_offense = int(np.random.choice([0, 1], p=[0.70, 0.30]))
            antecedents = int(np.random.choice([0, 1, 2, 3, 4], p=[0.60, 0.20, 0.10, 0.05, 0.05]))
            flight_risk = int(np.random.choice([0, 1], p=[0.80, 0.20]))
            amount_inr = float(np.random.choice([50000, 500000, 2500000, 12000000, 50000000]))
            recovery_ratio = float(np.random.uniform(0.0, 1.0))

            # Statutory Decision Simulation
            # Rule 1: Statutory default bail if custody > 60/90 days and no chargesheet
            if custody_days >= 60 and charge_sheet_filed == 0:
                outcome = 0  # Bail Granted (Statutory / Default)
            # Rule 2: Heinous crimes + prior records + high flight risk -> Custody Remand
            elif heinous_offense == 1 or (antecedents >= 2 and flight_risk == 1):
                outcome = 1  # Remand to Custody
            # Rule 3: High recovery ratio + frozen funds + chargesheet filed + low flight risk
            elif recovery_ratio > 0.70 and account_frozen == 1 and flight_risk == 0:
                outcome = 0  # Bail Granted
            # Rule 4: Digital evidence uncertified (no BSA 63) + custody > 30 days -> Interim relief
            elif statutory_cert == 0 and custody_days > 30 and antecedents == 0:
                outcome = 2  # Interim Relief
            # Rule 5: Heavy unrecovered financial exposure (> 1 Cr) with uncertified digital leads
            elif amount_inr > 10000000 and recovery_ratio < 0.20:
                outcome = 1  # Remand
            else:
                outcome = int(np.random.choice([0, 1, 2], p=[0.40, 0.45, 0.15]))

            records.append({
                "custody_duration_days": custody_days,
                "charge_sheet_filed": charge_sheet_filed,
                "account_frozen_indicator": account_frozen,
                "statutory_cert_present": statutory_cert,
                "heinous_offense_flag": heinous_offense,
                "prior_antecedents_count": antecedents,
                "flight_risk_indicator": flight_risk,
                "unauthorized_amount_inr": amount_inr,
                "recovery_effected_ratio": recovery_ratio,
                "judicial_outcome": outcome
            })

        return pd.DataFrame(records)

    def _train_and_save_model(self):
        """Auto-trains Random Forest classifier and persists model artifact."""
        df = self._generate_synthetic_judicial_data(10000)
        X = df[self.features]
        y = df["judicial_outcome"]

        X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        clf = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=4,
            random_state=42
        )
        clf.fit(X_train, y_train)

        os.makedirs(os.path.dirname(self.model_path) or ".", exist_ok=True)
        joblib.dump({
            "model": clf,
            "features": self.features,
            "outcome_mapping": self.outcome_mapping
        }, self.model_path)
        self.pipeline = clf

    def _ensure_model_ready(self):
        """Loads model artifact or triggers automatic synthetic training."""
        if os.path.exists(self.model_path):
            try:
                artifact = joblib.load(self.model_path)
                self.pipeline = artifact["model"]
                self.features = artifact["features"]
                self.outcome_mapping = artifact["outcome_mapping"]
            except Exception:
                self._train_and_save_model()
        else:
            self._train_and_save_model()

    # ==========================================
    # 2. INFERENCE & PROBABILITY EVALUATION
    # ==========================================
    def predict_judicial_relief(self, case_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates an accused's legal profile and predicts statutory bail/remand probability.
        """
        custody_days = int(case_params.get("custody_duration_days", 15))
        charge_sheet = int(case_params.get("charge_sheet_filed", 0))
        account_frozen = int(case_params.get("account_frozen_indicator", 1))
        statutory_cert = int(case_params.get("statutory_cert_present", 1))
        heinous = int(case_params.get("heinous_offense_flag", 0))
        antecedents = int(case_params.get("prior_antecedents_count", 0))
        flight_risk = int(case_params.get("flight_risk_indicator", 0))
        amount = float(case_params.get("unauthorized_amount_inr", 0))
        recovery_ratio = float(case_params.get("recovery_effected_ratio", 0.0))

        feat_vector = [
            custody_days, charge_sheet, account_frozen, statutory_cert,
            heinous, antecedents, flight_risk, amount, recovery_ratio
        ]

        if self.pipeline:
            # Pass input as a DataFrame with matching column names to eliminate sklearn feature-name warnings
            X_df = pd.DataFrame([feat_vector], columns=self.features)
            pred_class = int(self.pipeline.predict(X_df)[0])
            probabilities = self.pipeline.predict_proba(X_df)[0]
            confidence = float(np.max(probabilities))
            outcome_label = self.outcome_mapping.get(pred_class, "Remanded to Judicial Custody")
        else:
            # Fallback heuristic
            if custody_days >= 60 and charge_sheet == 0:
                pred_class, outcome_label, confidence = 0, "Bail Granted (Default Bail)", 0.95
            elif heinous == 1 or flight_risk == 1:
                pred_class, outcome_label, confidence = 1, "Remanded to Judicial Custody", 0.85
            else:
                pred_class, outcome_label, confidence = 2, "Interim Relief / Conditional Bail", 0.70

        # Extract legal grounds & risks
        legal_reasons = []
        if custody_days >= 60 and charge_sheet == 0:
            legal_reasons.append("STATUTORY_DEFAULT_BAIL (Section 187 BNSS / 167 CrPC milestone breach)")
        if statutory_cert == 0:
            legal_reasons.append("BSA_SECTION_63_ABSENT (Inadmissible electronic ledger hash)")
        if account_frozen == 1:
            legal_reasons.append("FINANCIAL_MITIGATION (Proceeds of crime frozen via 106 BNSS)")
        if flight_risk == 1:
            legal_reasons.append("FLIGHT_RISK_FLAG (High likelihood of absconding)")
        if heinous == 1:
            legal_reasons.append("ORGANIZED_SYNDICATE_OFFENSE (Non-bailable schedule under BNS 111/MCOCA)")

        return {
            "predicted_outcome_id": pred_class,
            "predicted_judicial_outcome": outcome_label,
            "confidence_score": round(confidence, 4),
            "custody_duration_days": custody_days,
            "statutory_compliance": {
                "chargesheet_timely": bool(charge_sheet),
                "bsa_section_63_certified": bool(statutory_cert),
                "accounts_frozen": bool(account_frozen)
            },
            "legal_milestone_reasons": legal_reasons
        }


if __name__ == "__main__":
    predictor = JudicialReliefPredictor()
    sample_case = {
        "custody_duration_days": 75,
        "charge_sheet_filed": 0,
        "account_frozen_indicator": 1,
        "statutory_cert_present": 1,
        "heinous_offense_flag": 0,
        "prior_antecedents_count": 0,
        "flight_risk_indicator": 0,
        "unauthorized_amount_inr": 3000000,
        "recovery_effected_ratio": 0.45
    }
    result = predictor.predict_judicial_relief(sample_case)
    print("\n[+] Judicial Predictor Result:")
    for k, v in result.items():
        print(f"  {k}: {v}")