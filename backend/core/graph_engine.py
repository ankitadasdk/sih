import os
import math
import joblib
import pandas as pd
import networkx as nx
from typing import Dict, Any, List, Optional

TYPE_COLOR_MAP = {
    "user": "#3b82f6",        # Soft Blue silhouette
    "account": "#0284c7",     # Light Blue / Cyan database
    "device": "#f97316",      # Orange device / server
    "transaction": "#ef4444"  # Crimson / Red transaction
}

class ConnectiveGraphEngine:
    def __init__(self, data_path: Optional[str] = None):
        self.models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
        self.model_path = os.path.join(self.models_dir, "connective_graph.pkl")
        
        if not data_path:
            candidates = [
                os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_crime_15k.csv"),
                os.path.join("data", "synthetic_crime_15k.csv"),
                "synthetic_crime_15k.csv"
            ]
            data_path = next((p for p in candidates if os.path.exists(p)), None)
        self.data_path = data_path
        self.G = nx.Graph()
        self._load_or_build_graph()

    def _load_or_build_graph(self):
        """Loads baseline network graph."""
        self.build_reference_network()

    def build_reference_network(self):
        """
        Constructs the exact master hub-and-spoke anti-fraud graph matching the reference image.
        Nodes: User 041, User 882, ACC-7741, 185.221.14.8, DEV-992A, ACC-1028, TXN-8831, ACC-5520, 10.42.8.64, DEV-174Q, TXN-8924, ACC-7015.
        Links: Solid grey, dotted grey, and yellow dashed/solid risk paths ("device trail", "velocity sig", "shared device").
        """
        self.G.clear()
        
        # 1. Define Nodes matching reference image exactly
        reference_nodes = [
            # Group 1 / Left Hub
            {"id": "User 041", "label": "User 041", "type": "user", "color": TYPE_COLOR_MAP["user"], "val": 18, "has_alert": True, "is_selected": False, "role": "Accused Suspect"},
            {"id": "ACC-7741", "label": "ACC-7741", "type": "account", "color": TYPE_COLOR_MAP["account"], "val": 22, "has_alert": True, "is_selected": False, "role": "Mule Bank Account"},
            {"id": "185.221.14.8", "label": "185.221.14.8", "type": "transaction", "color": TYPE_COLOR_MAP["transaction"], "val": 22, "has_alert": True, "is_selected": False, "role": "IP Proxy / Incident"},
            {"id": "DEV-992A", "label": "DEV-992A", "type": "device", "color": TYPE_COLOR_MAP["device"], "val": 22, "has_alert": True, "is_selected": False, "role": "SIM Box Gateway"},
            
            # Core Central Hub
            {"id": "ACC-1028", "label": "ACC-1028", "type": "account", "color": TYPE_COLOR_MAP["account"], "val": 26, "has_alert": True, "is_selected": False, "role": "Aggregator Account"},
            {"id": "User 882", "label": "User 882", "type": "user", "color": TYPE_COLOR_MAP["user"], "val": 18, "has_alert": True, "is_selected": False, "role": "Co-Conspirator"},
            {"id": "TXN-8831", "label": "TXN-8831", "type": "transaction", "color": TYPE_COLOR_MAP["transaction"], "val": 24, "has_alert": True, "is_selected": False, "role": "Unauthorized Exposure"},
            {"id": "ACC-5520", "label": "ACC-5520", "type": "account", "color": TYPE_COLOR_MAP["account"], "val": 22, "has_alert": True, "is_selected": False, "role": "Transit Ledger"},
            
            # High-Risk Cluster (Yellow Trails)
            {"id": "10.42.8.64", "label": "10.42.8.64", "type": "device", "color": TYPE_COLOR_MAP["device"], "val": 22, "has_alert": True, "is_selected": False, "role": "Vishing IP Hop"},
            {"id": "DEV-174Q", "label": "DEV-174Q", "type": "device", "color": TYPE_COLOR_MAP["device"], "val": 28, "has_alert": True, "is_selected": True, "role": "Mastermind Device"},
            {"id": "TXN-8924", "label": "TXN-8924", "type": "transaction", "color": TYPE_COLOR_MAP["transaction"], "val": 24, "has_alert": True, "is_selected": False, "role": "High-Velocity Txn"},
            {"id": "ACC-7015", "label": "ACC-7015", "type": "account", "color": TYPE_COLOR_MAP["account"], "val": 22, "has_alert": True, "is_selected": False, "role": "Cashout Account"}
        ]

        for n in reference_nodes:
            self.G.add_node(n["id"], **n)

        # 2. Define Links matching reference image layout
        reference_links = [
            # Dotted links connecting Users
            {"source": "User 041", "target": "ACC-7741", "relation": "", "color": "#475569", "dashed": False, "dotted": True, "weight": 1.2},
            {"source": "User 882", "target": "ACC-1028", "relation": "", "color": "#475569", "dashed": False, "dotted": True, "weight": 1.2},

            # Group 1 Mesh
            {"source": "ACC-7741", "target": "185.221.14.8", "relation": "", "color": "#475569", "dashed": False, "dotted": False, "weight": 1.5},
            {"source": "ACC-7741", "target": "ACC-1028", "relation": "", "color": "#475569", "dashed": False, "dotted": False, "weight": 1.5},
            {"source": "185.221.14.8", "target": "DEV-992A", "relation": "", "color": "#475569", "dashed": False, "dotted": False, "weight": 1.5},
            {"source": "185.221.14.8", "target": "ACC-1028", "relation": "", "color": "#475569", "dashed": False, "dotted": False, "weight": 1.5},
            {"source": "DEV-992A", "target": "ACC-1028", "relation": "", "color": "#475569", "dashed": False, "dotted": False, "weight": 1.5},

            # Secondary Hop to Dotted IP
            {"source": "DEV-992A", "target": "TXN-8831", "relation": "", "color": "#475569", "dashed": False, "dotted": True, "weight": 1.2},
            {"source": "ACC-1028", "target": "TXN-8831", "relation": "", "color": "#475569", "dashed": False, "dotted": False, "weight": 1.5},
            {"source": "TXN-8831", "target": "ACC-5520", "relation": "", "color": "#475569", "dashed": False, "dotted": False, "weight": 1.5},

            # Right Branch to High-Risk Target
            {"source": "ACC-5520", "target": "10.42.8.64", "relation": "", "color": "#475569", "dashed": False, "dotted": False, "weight": 1.5},
            {"source": "ACC-5520", "target": "TXN-8924", "relation": "", "color": "#475569", "dashed": False, "dotted": False, "weight": 1.5},

            # High-Risk Yellow Dashed Trails (DEV-174Q)
            {"source": "DEV-174Q", "target": "10.42.8.64", "relation": "device trail", "color": "#eab308", "dashed": True, "dotted": False, "weight": 2.0},
            {"source": "DEV-174Q", "target": "TXN-8924", "relation": "velocity sig", "color": "#eab308", "dashed": True, "dotted": False, "weight": 2.0},
            {"source": "DEV-174Q", "target": "ACC-7015", "relation": "shared device", "color": "#eab308", "dashed": False, "dotted": False, "weight": 2.5},

            # Connection from TXN-8924 to ACC-7015
            {"source": "TXN-8924", "target": "ACC-7015", "relation": "", "color": "#475569", "dashed": False, "dotted": False, "weight": 1.5}
        ]

        for l in reference_links:
            self.G.add_edge(
                l["source"],
                l["target"],
                relation=l.get("relation", ""),
                color=l.get("color", "#475569"),
                dashed=l.get("dashed", False),
                dotted=l.get("dotted", False),
                weight=l.get("weight", 1.5)
            )

    def get_full_topology(self) -> Dict[str, Any]:
        """Returns flat multi-entity topology nodes and links."""
        if self.G.number_of_nodes() == 0:
            self.build_reference_network()

        nodes = []
        for node_id, d in self.G.nodes(data=True):
            nodes.append({
                "id": str(node_id),
                "label": d.get("label", str(node_id)),
                "type": d.get("type", "account"),
                "color": d.get("color", TYPE_COLOR_MAP.get(d.get("type", "account"), "#0284c7")),
                "val": d.get("val", 20),
                "has_alert": d.get("has_alert", True),
                "is_selected": d.get("is_selected", False),
                "role": d.get("role", "Entity")
            })

        links = []
        for u, v, d in self.G.edges(data=True):
            links.append({
                "source": str(u),
                "target": str(v),
                "relation": d.get("relation", ""),
                "color": d.get("color", "#475569"),
                "dashed": d.get("dashed", False),
                "dotted": d.get("dotted", False),
                "weight": d.get("weight", 1.5)
            })

        return {
            "summary": {
                "total_entities": len(nodes),
                "total_relationships": len(links),
                "high_risk_alerts": sum(1 for n in nodes if n["has_alert"]),
                "kingpins_unmasked": sum(1 for n in nodes if n["is_selected"])
            },
            "nodes": nodes,
            "links": links
        }

    def get_entity_connections(self, person_id: str) -> Dict[str, Any]:
        """Queries 1st-degree operational links."""
        if person_id not in self.G:
            return {"error": f"Entity '{person_id}' not found in current network graph"}

        node_data = self.G.nodes[person_id]
        neighbors = []

        for neighbor in self.G.neighbors(person_id):
            edge_data = self.G.get_edge_data(person_id, neighbor)
            target_data = self.G.nodes[neighbor]

            neighbors.append({
                "connected_person_id": str(neighbor),
                "connected_label": target_data.get("label", str(neighbor)),
                "connected_type": target_data.get("type", "account"),
                "relationship": edge_data.get("relation", "LINKED_TO"),
                "relationship_weight": edge_data.get("weight", 1.0)
            })

        return {
            "person_id": str(person_id),
            "profile": node_data,
            "total_connections": len(neighbors),
            "relationships": neighbors
        }

if __name__ == "__main__":
    engine = ConnectiveGraphEngine()
    topo = engine.get_full_topology()
    print("[+] ConnectiveGraphEngine Topology Loaded:")
    print("  Total Nodes:", len(topo["nodes"]))
    print("  Total Links:", len(topo["links"]))