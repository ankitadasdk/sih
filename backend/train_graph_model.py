Here is the updated `train_graph_model.py` with duplicate imports cleaned up and the Louvain Community Detection block integrated into Step 5 without modifying the rest of the pipeline:

```python
import os
import sys
import math
import joblib
import pandas as pd
import numpy as np
import networkx as nx
from sklearn.neighbors import NearestNeighbors

def build_and_train_connective_model():
    # 1. Resolve Data Path
    candidate_paths = [
        os.path.join("data", "synthetic_crime_15k.csv"),
        os.path.join("data", "synthetic_crime_15k_cleaned.csv"),
        os.path.join("..", "data", "synthetic_crime_15k.csv"),
        "synthetic_crime_15k.csv",
    ]
    data_path = next((p for p in candidate_paths if os.path.exists(p)), None)

    if not data_path:
        print("[ERROR] Dataset not found in data/ folder!")
        sys.exit(1)

    print(f"[*] Loading dataset: {os.path.abspath(data_path)}")
    df = pd.read_csv(data_path)
    
    # We build the master relational network over the primary investigation batch (e.g. 500 representative nodes)
    sample_size = min(len(df), 500)
    df_sample = df.head(sample_size).copy()
    print(f"[*] Constructing Connective Model across {sample_size} primary entities...")

    G = nx.Graph()
    role_labels = {
        0: "Civilian / Uninvolved",
        1: "Ghost Kingpin",
        2: "Vishing Caller",
        3: "Tech Enabler / SIM Operator",
        4: "Money Mule Aggregator",
        5: "Field Cashier"
    }

    # 2. Ingest Nodes with Telemetry
    for idx, row in df_sample.iterrows():
        node_id = f"SUSPECT_{idx:04d}"
        role_id = int(row.get('label_entity_role', 0))
        
        G.add_node(
            node_id,
            node_id=node_id,
            label=f"{role_labels.get(role_id, 'Accused')} #{idx}",
            role_id=role_id,
            role_name=role_labels.get(role_id, "Unknown"),
            cases_alleged=int(row.get('number_of_cases_alleged', 1)),
            unauthorized_amount=float(row.get('unauthorized_transfer_amount_inr', 0)),
            night_call_ratio=float(row.get('night_call_ratio', 0)),
            call_burst_freq=int(row.get('call_burst_frequency', 0)),
            imei_swap_ratio=float(row.get('imei_sim_swap_ratio', 0)),
            velocity_mins=float(row.get('fund_transit_velocity_minutes', 0)) if pd.notnull(row.get('fund_transit_velocity_minutes')) else 0.0,
            fan_in_count=int(row.get('fan_in_count', 0)),
            account_frozen=int(row.get('account_frozen_indicator', 0))
        )

    # 3. Mine and Synthesize Relationship Edges
    print("[*] Mining inter-entity relationships & communication/financial edges...")
    nodes_data = list(G.nodes(data=True))

    kingpins = [n for n, d in nodes_data if d['role_id'] == 1]
    tech_ops = [n for n, d in nodes_data if d['role_id'] == 3]
    callers = [n for n, d in nodes_data if d['role_id'] == 2]
    mules = [n for n, d in nodes_data if d['role_id'] == 4]
    cashiers = [n for n, d in nodes_data if d['role_id'] == 5]

    # Rule A: Kingpin -> Tech Operators & Callers (Command Hierarchy)
    for kp in kingpins:
        for _ in range(min(2, len(tech_ops))):
            target = np.random.choice(tech_ops)
            G.add_edge(kp, target, relation="INSTRUCTS_INFRASTRUCTURE", weight=0.95, color="#ef4444")
        for _ in range(min(2, len(callers))):
            target = np.random.choice(callers)
            G.add_edge(kp, target, relation="COORDINATES_CALL_CAMPAIGN", weight=0.90, color="#f97316")

    # Rule B: Callers -> Tech Operators (SIM Gateway & VoIP routing)
    for caller in callers:
        if tech_ops:
            target_to = np.random.choice(tech_ops)
            G.add_edge(caller, target_to, relation="ROUTED_VIA_SIMBOX", weight=0.85, color="#eab308")

    # Rule C: Callers -> Money Mules (Victim Fund Diversion)
    for caller in callers:
        if mules:
            target_mule = np.random.choice(mules)
            G.add_edge(caller, target_mule, relation="DIVERTED_FUNDS_TO", weight=0.92, color="#06b6d4")

    # Rule D: Money Mule -> Money Mule (Rapid Fund Layering)
    for i in range(len(mules) - 1):
        if np.random.rand() > 0.4:
            G.add_edge(mules[i], mules[i+1], relation="MULE_TO_MULE_LAYERING", weight=0.98, color="#3b82f6")

    # Rule E: Money Mule -> Field Cashier (ATM Cash-out)
    for mule in mules:
        if cashiers and np.random.rand() > 0.5:
            target_cashier = np.random.choice(cashiers)
            G.add_edge(mule, target_cashier, relation="ATM_CASH_WITHDRAWAL", weight=0.88, color="#a855f7")

    # 4. Behavioral Feature Similarity Linking (k-NN Co-Offender Clustering)
    feature_matrix = []
    node_keys = []
    for n, d in nodes_data:
        feature_matrix.append([
            d['night_call_ratio'],
            d['call_burst_freq'],
            d['imei_swap_ratio'],
            d['velocity_mins'],
            d['fan_in_count']
        ])
        node_keys.append(n)

    knn = NearestNeighbors(n_neighbors=3, metric='cosine')
    knn.fit(feature_matrix)
    distances, indices = knn.kneighbors(feature_matrix)

    for i, neighbors in enumerate(indices):
        u = node_keys[i]
        for j, neighbor_idx in enumerate(neighbors[1:]): # skip self
            v = node_keys[neighbor_idx]
            dist = distances[i][j+1]
            if dist < 0.15 and not G.has_edge(u, v):
                G.add_edge(u, v, relation="SHARED_MODUS_OPERANDI", weight=round(1.0 - dist, 3), color="#10b981")

    # 5. Compute Graph Topologies & Topological Kingpin Metric
    print("[*] Computing Betweenness, Degree, and Kingpin Scores...")
    degrees = dict(G.degree())
    betweenness = nx.betweenness_centrality(G)

    for node_id in G.nodes():
        deg = degrees[node_id]
        bet = betweenness[node_id]
        kp_score = bet / math.log(1 + deg) if deg > 0 else 0.0
        
        G.nodes[node_id]['degree'] = deg
        G.nodes[node_id]['betweenness'] = round(bet, 4)
        G.nodes[node_id]['topological_kingpin_score'] = round(kp_score, 4)
        G.nodes[node_id]['is_unmasked_kingpin'] = bool(kp_score > 0.20 and G.nodes[node_id]['role_id'] == 1)

    # 5b. Louvain Syndicate Cell Community Detection
    print("[*] Performing Louvain Community Detection to segment syndicate cells...")
    communities = nx.community.louvain_communities(G, seed=42)
    print(f"[*] Detected {len(communities)} distinct operational syndicate cells.")

    for cell_idx, cell_members in enumerate(communities):
        cell_tag = f"CELL_{cell_idx + 1:02d}"
        for member in cell_members:
            G.nodes[member]['syndicate_cell_id'] = cell_tag

    # 6. Save Model Artifact
    os.makedirs("models", exist_ok=True)
    out_path = os.path.join("models", "connective_graph.pkl")
    joblib.dump(G, out_path)
    
    print("\n" + "="*60)
    print(f"[SUCCESS] Connective Model Fitted & Exported to {out_path}")
    print(f"Total Entity Nodes: {G.number_of_nodes()}")
    print(f"Total Relationship Edges: {G.number_of_edges()}")
    print(f"Total Syndicate Cells: {len(communities)}")
    print(f"Ghost Kingpins Isolated: {sum(1 for _, d in G.nodes(data=True) if d.get('is_unmasked_kingpin'))}")
    print("="*60)

if __name__ == "__main__":
    build_and_train_connective_model()

```