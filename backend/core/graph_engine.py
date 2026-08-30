import os
import math
import joblib
import pandas as pd
import networkx as nx
from typing import Dict, Any, List, Optional

class ConnectiveGraphEngine:
    def __init__(self, data_path: Optional[str] = None):
        self.models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
        self.model_path = os.path.join(self.models_dir, "connective_graph.pkl")
        
        # Locate fallback CSV path
        if not data_path:
            candidates = [
                os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_crime_15k.csv"),
                os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_crime_15k_cleaned.csv"),
                os.path.join("data", "synthetic_crime_15k.csv"),
                "synthetic_crime_15k.csv"
            ]
            data_path = next((p for p in candidates if os.path.exists(p)), None)
        self.data_path = data_path

        self.role_map = {
            0: "Civilian / Uninvolved",
            1: "Ghost Kingpin",
            2: "Vishing Caller",
            3: "Tech Enabler",
            4: "Money Mule",
            5: "Field Cashier"
        }

        self.G = nx.Graph()
        self._load_or_build_graph()

    def _load_or_build_graph(self):
        """Loads serialized graph if available; otherwise dynamically constructs baseline network."""
        if os.path.exists(self.model_path):
            try:
                self.G = joblib.load(self.model_path)
                return
            except Exception as e:
                print(f"[WARN] Failed to load {self.model_path}: {e}. Falling back to CSV build.")
        
        self.build_network_from_csv(max_samples=120)

    def build_network_from_csv(self, max_samples: int = 120):
        """Constructs and annotates the relational graph directly from dataset records."""
        self.G.clear()
        if not self.data_path or not os.path.exists(self.data_path):
            return

        df = pd.read_csv(self.data_path).head(max_samples)

        # 1. Ingest Nodes
        for idx, row in df.iterrows():
            node_id = f"SUSPECT_{idx:04d}"
            role_id = int(row.get('label_entity_role', 0))
            self.G.add_node(
                node_id,
                node_id=node_id,
                label=f"{self.role_map.get(role_id, 'Accused')} #{idx}",
                role_id=role_id,
                role_name=self.role_map.get(role_id, "Unknown"),
                cases_alleged=int(row.get('number_of_cases_alleged', 1)),
                unauthorized_amount=float(row.get('unauthorized_transfer_amount_inr', 0)),
                is_kingpin=(role_id == 1)
            )

        # 2. Add Relational Edges
        nodes = list(self.G.nodes(data=True))
        kingpins = [n for n, d in nodes if d.get('role_id') == 1]
        tech_ops = [n for n, d in nodes if d.get('role_id') == 3]
        callers = [n for n, d in nodes if d.get('role_id') == 2]
        mules = [n for n, d in nodes if d.get('role_id') == 4]
        cashiers = [n for n, d in nodes if d.get('role_id') == 5]

        # Kingpin Control links
        for kp in kingpins:
            if tech_ops:
                target_to = tech_ops[hash(kp) % len(tech_ops)]
                self.G.add_edge(kp, target_to, relation="INSTRUCTS_CELL", weight=0.95, color="#ef4444")
            if callers:
                target_caller = callers[hash(kp) % len(callers)]
                self.G.add_edge(kp, target_caller, relation="COORDINATES_CALL_CAMPAIGN", weight=0.90, color="#f97316")

        # Caller to SIM Operator
        for idx, caller in enumerate(callers):
            if tech_ops:
                to = tech_ops[idx % len(tech_ops)]
                self.G.add_edge(caller, to, relation="ROUTED_VIA_SIMBOX", weight=0.85, color="#eab308")

        # Caller to Mule Diversion
        for idx, caller in enumerate(callers):
            if mules:
                mule = mules[idx % len(mules)]
                self.G.add_edge(caller, mule, relation="DIVERTED_FUNDS_TO", weight=0.92, color="#06b6d4")

        # Mule-to-Mule Layering
        for i in range(len(mules) - 1):
            if i % 2 == 0:
                self.G.add_edge(mules[i], mules[i+1], relation="MULE_TO_MULE_LAYERING", weight=0.98, color="#3b82f6")

        # Mule to Cashier ATM Drop
        for idx, collector in enumerate(cashiers):
            if mules:
                mule = mules[idx % len(mules)]
                self.G.add_edge(mule, collector, relation="ATM_CASH_WITHDRAWAL", weight=0.88, color="#a855f7")

        # 3. Graph Centrality Calculation
        degree_dict = dict(self.G.degree())
        betweenness_dict = nx.betweenness_centrality(self.G)

        for node_id in self.G.nodes():
            deg = degree_dict.get(node_id, 0)
            bet = betweenness_dict.get(node_id, 0.0)
            kp_score = bet / math.log(1 + deg) if deg > 0 else 0.0
            
            self.G.nodes[node_id]['degree'] = deg
            self.G.nodes[node_id]['betweenness'] = round(bet, 4)
            self.G.nodes[node_id]['topological_kingpin_score'] = round(kp_score, 4)
            self.G.nodes[node_id]['is_unmasked_kingpin'] = bool(
                self.G.nodes[node_id].get('is_kingpin') or (kp_score > 0.20 and self.G.nodes[node_id]['role_id'] == 1)
            )

    def get_full_topology(self) -> Dict[str, Any]:
        """Returns all nodes and relationship edges for network canvas rendering."""
        if self.G.number_of_nodes() == 0:
            self._load_or_build_graph()

        nodes = []
        for node_id, d in self.G.nodes(data=True):
            role_id = d.get("role_id", 0)
            nodes.append({
                "id": str(node_id),
                "label": d.get("label", str(node_id)),
                "role": d.get("role_name", self.role_map.get(role_id, "Unknown")),
                "role_id": role_id,
                "degree": d.get("degree", self.G.degree(node_id)),
                "betweenness": d.get("betweenness", 0.0),
                "kingpin_score": d.get("topological_kingpin_score", 0.0),
                "is_likely_kingpin": d.get("is_unmasked_kingpin", role_id == 1),
                "unauthorized_amount": d.get("unauthorized_amount", 0.0),
                "cases_alleged": d.get("cases_alleged", 1)
            })

        links = [
            {
                "source": str(u),
                "target": str(v),
                "relation": d.get("relation", "CONNECTED_TO"),
                "weight": d.get("weight", 1.0),
                "color": d.get("color", "#64748b")
            }
            for u, v, d in self.G.edges(data=True)
        ]

        return {
            "summary": {
                "total_entities": len(nodes),
                "total_relationships": len(links),
                "kingpins_unmasked": sum(1 for n in nodes if n["is_likely_kingpin"])
            },
            "nodes": nodes,
            "links": links
        }

    def get_entity_connections(self, person_id: str) -> Dict[str, Any]:
        """Queries immediate 1st-degree operational links for a target suspect."""
        if person_id not in self.G:
            return {"error": f"Person '{person_id}' not found in current network graph"}

        node_data = self.G.nodes[person_id]
        neighbors = []

        for neighbor in self.G.neighbors(person_id):
            edge_data = self.G.get_edge_data(person_id, neighbor)
            target_data = self.G.nodes[neighbor]
            target_role_id = target_data.get("role_id", 0)

            neighbors.append({
                "connected_person_id": str(neighbor),
                "connected_label": target_data.get("label", str(neighbor)),
                "connected_role": target_data.get("role_name", self.role_map.get(target_role_id, "Unknown")),
                "relationship": edge_data.get("relation", "CONNECTED_TO"),
                "relationship_weight": edge_data.get("weight", 1.0)
            })

        return {
            "person_id": str(person_id),
            "profile": {
                "label": node_data.get("label", str(person_id)),
                "role": node_data.get("role_name", self.role_map.get(node_data.get("role_id", 0), "Unknown")),
                "degree": node_data.get("degree", self.G.degree(person_id)),
                "betweenness": node_data.get("betweenness", 0.0),
                "kingpin_score": node_data.get("topological_kingpin_score", 0.0),
                "is_likely_kingpin": node_data.get("is_unmasked_kingpin", False)
            },
            "total_connections": len(neighbors),
            "relationships": neighbors
        }