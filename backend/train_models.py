import os
import sys
import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

def main():
    # 1. Resolve Dataset Path
    candidate_paths = [
        os.path.join("data", "synthetic_crime_15k.csv"),
        os.path.join("data", "synthetic_crime_15k_cleaned.csv"),
        os.path.join("..", "data", "synthetic_crime_15k.csv"),
        os.path.join("..", "data", "synthetic_crime_15k_cleaned.csv"),
        "synthetic_crime_15k.csv",
    ]

    data_path = next((p for p in candidate_paths if os.path.exists(p)), None)

    if not data_path:
        print("\n[ERROR] Could not locate the dataset file!")
        print(f"Current Working Directory: {os.getcwd()}")
        print(f"Checked paths: {candidate_paths}")
        sys.exit(1)

    print(f"[*] Loading dataset from: {os.path.abspath(data_path)}")
    df = pd.read_csv(data_path)
    print(f"[*] Dataset loaded successfully with shape: {df.shape}")

    # 2. Prune Target Leakage, Clones & Identifiers
    drop_cols = [
        'label_public_order_vs_law_and_order',
        'ipc_468_471',
        'cybercrime_indicator',
        'case_reference_id'
    ]
    df_clean = df.drop(columns=[c for c in drop_cols if c in df.columns])
    print(f"[*] Pruned leakage columns. Clean feature count: {df_clean.shape[1]}")

    # Ensure output models directory exists
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)

    # -------------------------------------------------------------------------
    # 3. Model 1: Suspicion Engine (Entity Role Multi-Class 0-5)
    # -------------------------------------------------------------------------
    print("\n" + "="*60)
    print("Training Model 1: Suspicion Engine (Entity Role Classifier)")
    print("="*60)
    
    target_role = 'label_entity_role'
    other_targets = [
        'label_high_risk_cyber_syndicate', 
        'label_bail_or_custody_relief', 
        'label_conviction_outcome'
    ]

    # Drop target and other label columns from feature matrix
    X_role = df_clean.drop(columns=[target_role] + [c for c in other_targets if c in df_clean.columns])
    
    # One-hot encode any string metadata columns
    cat_cols = [c for c in ['court_level', 'case_type'] if c in X_role.columns]
    if cat_cols:
        X_role = pd.get_dummies(X_role, columns=cat_cols, drop_first=True)

    y_role = df_clean[target_role]

    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
        X_role, y_role, test_size=0.2, stratify=y_role, random_state=42
    )

    role_model = HistGradientBoostingClassifier(
        max_depth=6,
        learning_rate=0.1,
        max_iter=150,
        random_state=42
    )
    role_model.fit(X_train_r, y_train_r)

    y_pred_r = role_model.predict(X_test_r)
    role_report = classification_report(y_test_r, y_pred_r, digits=4)
    print("\nSuspicion Engine Test Performance:")
    print(role_report)

    # Save artifacts
    joblib.dump(role_model, os.path.join(models_dir, "suspicion_engine.pkl"))
    joblib.dump(list(X_role.columns), os.path.join(models_dir, "role_features.pkl"))
    print(f"[✓] Saved: {models_dir}/suspicion_engine.pkl")
    print(f"[✓] Saved: {models_dir}/role_features.pkl")

    # -------------------------------------------------------------------------
    # 4. Model 2: Judicial Relief Predictor (Bail Interaction Model)
    # -------------------------------------------------------------------------
    print("\n" + "="*60)
    print("Training Model 2: Judicial Relief Predictor (Bail Risk Model)")
    print("="*60)

    target_bail = 'label_bail_or_custody_relief'
    bail_feature_candidates = [
        'custody_duration_days',
        'charge_sheet_filed',
        'account_frozen_indicator',
        'statutory_cert_present',
        'evidence_completeness_score',
        'chain_of_custody_complete'
    ]
    bail_features = [f for f in bail_feature_candidates if f in df_clean.columns]

    X_bail = df_clean[bail_features]
    y_bail = df_clean[target_bail]

    X_train_b, X_test_b, y_train_b, y_test_b = train_test_split(
        X_bail, y_bail, test_size=0.2, stratify=y_bail, random_state=42
    )

    bail_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
        random_state=42
    )
    bail_model.fit(X_train_b, y_train_b)

    y_pred_b = bail_model.predict(X_test_b)
    bail_report = classification_report(y_test_b, y_pred_b, digits=4)
    print("\nJudicial Predictor Test Performance:")
    print(bail_report)

    # Save artifacts
    joblib.dump(bail_model, os.path.join(models_dir, "judicial_predictor.pkl"))
    joblib.dump(bail_features, os.path.join(models_dir, "bail_features.pkl"))
    print(f"[✓] Saved: {models_dir}/judicial_predictor.pkl")
    print(f"[✓] Saved: {models_dir}/bail_features.pkl")

    print("\n" + "="*60)
    print("[SUCCESS] All models trained and saved to backend/models/!")
    print("="*60)

if __name__ == "__main__":
    main()