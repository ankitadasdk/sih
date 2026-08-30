import os
import math
import joblib
import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, Any, List
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split

ROLE_MAPPING = {
    0: "Civilian / Uninvolved",
    1: "Ghost Kingpin",
    2: "Vishing Caller",
    3: "Tech Enabler",
    4: "Money Mule",
    5: "Field Cashier"
}

FEATURE_COLS = [
    "betweenness_centrality", "degree", "night_call_ratio", 
    "call_burst_frequency", "sim_swap_count", "imei_churn_rate", 
    "voip_proxy_ratio", "transit_velocity_mins", "fan_in_account_ratio", 
    "atm_cashout_velocity", "unauthorized_exposure_inr", "fastag_crossings"
]


class SuspicionScoringEngine:
    def __init__(self, model_path: str = "models/suspicion_engine.pkl"):
        self.model_path = model_path
        self.pipeline = None
        self.features = FEATURE_COLS
        self.role_mapping = ROLE_MAPPING
        self._ensure_model_ready()

    # ==========================================
    # 1. AUTO-TRAINING & DATASET GENERATION
    # ==========================================
    def _generate_synthetic_syndicate_data(self, n_samples: int = 12000) -> pd.DataFrame:
        """Synthesizes multi-modal behavioral, telephony, financial, and graph telemetry."""
        np.random.seed(42)
        records = []

        for _ in range(n_samples):
            role = np.random.choice([0, 1, 2, 3, 4, 5], p=[0.35, 0.05, 0.20, 0.10, 0.20, 0.10])
            
            # Baseline parameters
            betweenness_centrality = np.random.uniform(0.0, 0.02)
            degree = np.random.randint(1, 4)
            night_call_ratio = np.random.uniform(0.01, 0.15)
            call_burst_frequency = np.random.uniform(1.0, 5.0)
            sim_swap_count = np.random.randint(1, 2)
            imei_churn_rate = np.random.uniform(0.0, 0.1)
            voip_proxy_ratio = np.random.uniform(0.0, 0.05)
            transit_velocity_mins = np.random.uniform(120, 1440)
            fan_in_account_ratio = np.random.uniform(0.0, 0.1)
            atm_cashout_velocity = np.random.uniform(0.0, 0.1)
            unauthorized_exposure_inr = np.random.uniform(0, 50000)
            fastag_crossings = np.random.randint(0, 2)
            
            # Syndicate behavioral signatures
            if role == 1:  # Ghost Kingpin
                betweenness_centrality = np.random.uniform(0.18, 0.95)
                degree = np.random.randint(2, 6)
                unauthorized_exposure_inr = np.random.uniform(5000000, 50000000)
                voip_proxy_ratio = np.random.uniform(0.60, 0.99)
                sim_swap_count = np.random.randint(2, 5)
                
            elif role == 2:  # Vishing Caller
                night_call_ratio = np.random.uniform(0.50, 0.95)
                call_burst_frequency = np.random.uniform(40.0, 150.0)
                degree = np.random.randint(8, 30)
                voip_proxy_ratio = np.random.uniform(0.40, 0.90)
                
            elif role == 3:  # Tech Enabler
                sim_swap_count = np.random.randint(6, 25)
                imei_churn_rate = np.random.uniform(0.70, 1.0)
                degree = np.random.randint(5, 18)
                voip_proxy_ratio = np.random.uniform(0.75, 1.0)
                
            elif role == 4:  # Money Mule
                transit_velocity_mins = np.random.uniform(0.5, 9.5)
                fan_in_account_ratio = np.random.uniform(0.65, 0.99)
                unauthorized_exposure_inr = np.random.uniform(500000, 10000000)
                betweenness_centrality = np.random.uniform(0.05, 0.25)
                
            elif role == 5:  # Field Cashier
                atm_cashout_velocity = np.random.uniform(0.70, 1.0)
                fastag_crossings = np.random.randint(4, 15)
                transit_velocity_mins = np.random.uniform(5.0, 30.0)
                unauthorized_exposure_inr = np.random.uniform(100000, 2000000)

            records.append({
                "betweenness_centrality": betweenness_centrality,
                "degree": degree,
                "night_call_ratio": night_call_ratio,
                "call_burst_frequency": call_burst_frequency,
                "sim_swap_count": sim_swap_count,
                "imei_churn_rate": imei_churn_rate,
                "voip_proxy_ratio": voip_proxy_ratio,
                "transit_velocity_mins": transit_velocity_mins,
                "fan_in_account_ratio": fan_in_account_ratio,
                "atm_cashout_velocity": atm_cashout_velocity,
                "unauthorized_exposure_inr": unauthorized_exposure_inr,
                "fastag_crossings": fastag_crossings,
                "syndicate_role": role
            })

        return pd.DataFrame(records)

    def _train_and_save_model(self):
        """Auto-trains HistGradientBoosting model and saves to disk."""
        df = self._generate_synthetic_syndicate_data(12000)
        X = df[self.features]
        y = df["syndicate_role"]

        X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        clf = HistGradientBoostingClassifier(
            max_iter=200,
            learning_rate=0.08,
            max_leaf_nodes=31,
            random_state=42
        )
        clf.fit(X_train, y_train)

        os.makedirs(os.path.dirname(self.model_path) or ".", exist_ok=True)
        joblib.dump({"model": clf, "features": self.features, "role_mapping": self.role_mapping}, self.model_path)
        self.pipeline = clf

    def _ensure_model_ready(self):
        """Loads model from disk or triggers auto-training."""
        if os.path.exists(self.model_path):
            try:
                artifact = joblib.load(self.model_path)
                self.pipeline = artifact["model"]
                self.features = artifact["features"]
                self.role_mapping = artifact["role_mapping"]
            except Exception:
                self._train_and_save_model()
        else:
            self._train_and_save_model()

    # ==========================================
    # 2. FEATURE EXTRACTION & INFERENCE
    # ==========================================
    def extract_feature_vector(self, node_attributes: Dict[str, Any], G: nx.Graph, node_id: str) -> List[float]:
        """Extracts 12-dimensional feature vector for a specific node."""
        degree = G.degree(node_id) if G.has_node(node_id) else 1
        betweenness_dict = nx.betweenness_centrality(G) if len(G.nodes) > 2 else {node_id: 0.0}
        betweenness = betweenness_dict.get(node_id, 0.0)

        intercepts = node_attributes.get("telecom_intercepts", {})
        telemetry = node_attributes.get("financial_telemetry", {})
        amount = float(node_attributes.get("unauthorized_amount", 0))
        sub_nodes = node_attributes.get("sub_nodes", [])

        total_calls = intercepts.get("total_calls", 0) if intercepts else 0
        burst_str = intercepts.get("burst_window", "").lower() if intercepts else ""
        night_call_ratio = 0.85 if ("night" in burst_str or "01:" in burst_str or "23:" in burst_str) else 0.10
        call_burst_frequency = float(total_calls) if total_calls > 0 else 2.0
        
        sim_count = max(1, sum(1 for sn in sub_nodes if sn.get("role_id") == 6))
        imei_churn_rate = 0.85 if sim_count > 1 else 0.05
        voip_proxy_ratio = 0.90 if "voip" in burst_str else 0.05

        transit_velocity_str = telemetry.get("transit_velocity", "").lower() if telemetry else ""
        transit_velocity_mins = 4.5 if any(k in transit_velocity_str for k in ["< 5", "< 10", "rapid", "immediate"]) else 240.0
        
        obs_tx = telemetry.get("observed_tx_count", "").lower() if telemetry else ""
        fan_in_account_ratio = 0.90 if "layering" in obs_tx else 0.10
        atm_cashout_velocity = 0.85 if "cash" in obs_tx else 0.05

        conclusion_str = node_attributes.get("investigative_conclusion", "").lower()
        fastag_crossings = 8 if any(k in conclusion_str for k in ["fastag", "border", "corridor"]) else 0

        return [
            betweenness,
            degree,
            night_call_ratio,
            call_burst_frequency,
            sim_count,
            imei_churn_rate,
            voip_proxy_ratio,
            transit_velocity_mins,
            fan_in_account_ratio,
            atm_cashout_velocity,
            amount,
            fastag_crossings
        ]

    def predict_suspect_role(self, node_attributes: Dict[str, Any], G: nx.Graph, node_id: str) -> Dict[str, Any]:
        """Runs HistGradientBoosting inference on suspect telemetry."""
        feat_vector = self.extract_feature_vector(node_attributes, G, node_id)

        if self.pipeline:
            X = np.array([feat_vector])
            pred_class = int(self.pipeline.predict(X)[0])
            probabilities = self.pipeline.predict_proba(X)[0]
            confidence = float(np.max(probabilities))
            predicted_role = self.role_mapping.get(pred_class, "Civilian / Uninvolved")
        else:
            pred_class, predicted_role, confidence = 0, "Civilian / Uninvolved", 0.50

        is_kingpin = (pred_class == 1)
        risk_tier = "CRITICAL_RED" if pred_class in [1, 2] else ("HIGH_AMBER" if pred_class in [3, 4, 5] else "LOW_GREEN")

        return {
            "classified_role_id": pred_class,
            "classified_syndicate_role": predicted_role,
            "classification_confidence": round(confidence, 4),
            "risk_tier": risk_tier,
            "is_likely_kingpin": is_kingpin,
            "telemetry_metrics": {
                "betweenness_centrality": round(feat_vector[0], 4),
                "graph_degree": feat_vector[1],
                "transit_velocity_mins": feat_vector[7],
                "call_burst_frequency": feat_vector[3]
            }
        }

    # ==========================================
    # 3. FULL NETWORK GRAPH PIPELINE
    # ==========================================
    def score_entire_network(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Classifies every node across the complete graph topology."""
        nodes = graph_data.get("nodes", [])
        links = graph_data.get("links", [])

        G = nx.Graph()
        for n in nodes:
            G.add_node(n["id"], **n)

        for l in links:
            src = l["source"]["id"] if isinstance(l["source"], dict) else l["source"]
            tgt = l["target"]["id"] if isinstance(l["target"], dict) else l["target"]
            if G.has_node(src) and G.has_node(tgt):
                G.add_edge(src, tgt)

        TYPE_COLOR_MAP = {
            "user": "#3b82f6",
            "account": "#0284c7",
            "device": "#f97316",
            "transaction": "#ef4444"
        }

        scored_nodes = []
        for n in nodes:
            node_copy = dict(n)
            # Preserve multi-entity type and color if already specified
            if "type" in node_copy and node_copy["type"] in TYPE_COLOR_MAP:
                node_copy["color"] = TYPE_COLOR_MAP[node_copy["type"]]
            elif "color" not in node_copy:
                node_copy["color"] = "#0284c7"
            
            # Predict suspect role telemetry if applicable
            try:
                prediction = self.predict_suspect_role(n, G, n["id"])
                node_copy["role_id"] = prediction["classified_role_id"]
                node_copy["confidence"] = prediction["classification_confidence"]
                node_copy["risk_tier"] = prediction["risk_tier"]
                node_copy["is_likely_kingpin"] = prediction["is_likely_kingpin"]
            except Exception:
                pass

            scored_nodes.append(node_copy)

        return {
            "summary": graph_data.get("summary", {}),
            "nodes": scored_nodes,
            "links": links
        }


# Allows running `python suspicion_engine.py` directly to force-train and verify
if __name__ == "__main__":
    engine = SuspicionScoringEngine()
    print("[+] SuspicionScoringEngine initialized & ready. Model status:", engine.pipeline is not None)