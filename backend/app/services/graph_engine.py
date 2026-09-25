import re
import networkx as nx
import community.community_louvain as community_louvain
from typing import List, Dict, Any

class GraphEngineService:
    def __init__(self):
        self.graph = nx.Graph()
        # Optional ML Forensics Service Loader with graceful fallback
        try:
            from app.services.ml_service import MLForensicsService
            self.ml_service = MLForensicsService()
        except Exception:
            self.ml_service = None

    def construct_graph(self, nodes: List[Dict[str, Any]], links: List[Dict[str, Any]]) -> None:
        """
        Dynamically constructs the NetworkX Graph preserving all dynamic payload attributes,
        call volumes, timestamps, and legal sections.
        """
        self.graph.clear()
        for node in nodes:
            node_attrs = {k: v for k, v in node.items() if k != "id"}
            self.graph.add_node(node["id"], **node_attrs)

        for link in links:
            source = link["source"]
            target = link["target"]
            edge_attrs = {k: v for k, v in link.items() if k not in ["source", "target"]}
            
            # Dynamic default edge weight derived from session counts
            call_count = int(link.get("call_count", 1)) if link.get("call_count") is not None else 1
            edge_attrs.setdefault("call_count", call_count)
            edge_attrs.setdefault("weight", float(link.get("weight", max(1.0, float(call_count) * 0.25))))
            edge_attrs.setdefault("relationship", link.get("relationship", "ASSOCIATED_WITH"))
            edge_attrs.setdefault("label", edge_attrs["relationship"])
            edge_attrs.setdefault("timestamp", link.get("timestamp", ""))

            self.graph.add_edge(source, target, **edge_attrs)

    @staticmethod
    def classify_command_hierarchy(
        n_id: str,
        data: Dict[str, Any],
        degree: int,
        betweenness: float,
        pagerank: float,
        total_suspects: int
    ) -> Dict[str, Any]:
        """
        Mathematically isolates:
        1. SURVEILLANCE_TARGET: The explicit primary wiretap focus or FIR trigger point.
        2. APPARENT_KINGPIN (Field Boss / Hub): High degree, high betweenness, high communication volume.
        3. ACTUAL_KINGPIN (Shadow Mastermind): Low degree (strict OPSEC / air-gapped), low betweenness,
            but Highest PageRank (Eigenvector authority) linking only to key controllers.
        """
        node_type = data.get("type", "PERSON")
        details = data.get("details", {})
        sections = details.get("sections", [])
        sec_str = " ".join([str(s) for s in sections]).lower()

        is_critical_flag = details.get("is_critical", False)
        is_primary_target = details.get("is_primary_target", False) or "target" in data.get("name", "").lower()
        has_heinous_charge = bool(re.search(r'\b(103|302|111|mcoca|uapa|arms|25)\b', sec_str))

        # --- CLASS A: ACTUAL KINGPIN (Shadow Mastermind) ---
        is_shadow_mastermind = (
            node_type == "PERSON" and
            pagerank >= 0.08 and
            degree <= max(2, int(total_suspects * 0.45)) and
            betweenness <= 0.25 and
            (has_heinous_charge or is_critical_flag)
        )

        if is_shadow_mastermind:
            return {
                "hierarchy_class": "ACTUAL_KINGPIN",
                "ml_role": "Actual Kingpin (Shadow Mastermind)",
                "color": "#ef4444",    # Fixed to match Kingpin Red Legend (#ef4444)
                "size_boost": 18.0,
                "threat_bias": 0.92,
                "is_kingpin": True
            }

        # --- CLASS B: APPARENT_KINGPIN (Operational Hub / Enforcer Front) ---
        is_hub_commander = (
            node_type == "PERSON" and
            (betweenness >= 0.20 or degree >= 4) and
            pagerank >= 0.06
        )

        if is_hub_commander:
            return {
                "hierarchy_class": "APPARENT_KINGPIN",
                "ml_role": "Apparent Kingpin (Operational Hub / Field Boss)",
                "color": "#f59e0b",    # Fixed to match Apparent Kingpin Amber Legend (#f59e0b)
                "size_boost": 12.0,
                "threat_bias": 0.76,
                "is_kingpin": False    
            }

        # --- CLASS C: SURVEILLANCE TARGET (Primary Intercept Focal Point) ---
        if is_primary_target or details.get("is_intercepted", False):
            return {
                "hierarchy_class": "SURVEILLANCE_TARGET",
                "ml_role": details.get("role") or "Active Surveillance Target",
                "color": "#06b6d4",    # Fixed to match Surveillance Target Cyan Legend (#06b6d4)
                "size_boost": 8.0,
                "threat_bias": 0.60,
                "is_kingpin": False
            }

        # --- CLASS D: OPERATIONAL SUSPECT / MULE / ASSOCIATE ---
        return {
            "hierarchy_class": "OPERATIONAL_NODE",
            "ml_role": details.get("role") or "Suspect Associate",
            "color": "#a855f7",        # Fixed to match Suspects & Operatives Purple Legend (#a855f7)
            "size_boost": 2.0,
            "threat_bias": 0.20,
            "is_kingpin": False
        }

    def _propagate_peripheral_threat(self, human_threats: Dict[str, float]) -> Dict[str, float]:
        propagated = {}
        for n_id, data in self.graph.nodes(data=True):
            if data.get("type") == "PERSON":
                continue

            neighbors = list(self.graph.neighbors(n_id))
            if not neighbors:
                propagated[n_id] = 0.10
                continue

            scores = []
            for nbr in neighbors:
                nbr_risk = human_threats.get(nbr, 0.15)
                edge_data = self.graph.get_edge_data(n_id, nbr)
                call_count = float(edge_data.get("call_count", 1))
                
                interaction_factor = min(1.8, 1.0 + (call_count / 15.0))
                scores.append(nbr_risk * interaction_factor * 0.45)

            max_score = max(scores) if scores else 0.10
            propagated[n_id] = round(min(0.65, max(0.10, max_score)), 3)

        return propagated

    @staticmethod
    def determine_statutory_bail(
        sections: list,
        hierarchy_class: str,
        suspect_role: str = "",
        threat_score: float = 0.0
    ) -> str:
        sec_str = " ".join([str(s) for s in sections]).lower()
        role_lower = str(suspect_role).lower()

        if hierarchy_class == "ACTUAL_KINGPIN":
            return "Non-Bailable (Shadow Mastermind / High Flight Risk)"

        capital_offences = ["103", "302", "307", "395", "397", "386", "70", "376"]
        if any(bool(re.search(rf'\b{c}\b', sec_str)) for c in capital_offences):
            if any(bool(re.search(rf'\b{c}\b', sec_str)) for c in ["103", "302"]):
                return "Non-Bailable (Capital Offence / Sec 103 BNS)"
            return "Non-Bailable (Statutory Bar / Schedule I BNSS)"

        if hierarchy_class == "APPARENT_KINGPIN" and any(bool(re.search(rf'\b{w}\b', sec_str)) for w in ["111", "arms", "25"]):
            return "Non-Bailable (Operational Hub / Firearm Syndicate)"

        if hierarchy_class == "OPERATIONAL_NODE" and (threat_score <= 0.30 or any(r in role_lower for r in ["mule", "courier", "associate", "peripheral"])):
            return "Bailable (Statutory Right / Associate Tier)"

        if any(bool(re.search(rf'\b{s}\b', sec_str)) for s in ["111", "mcoca", "मकोका", "uapa", "यूएपीए"]):
            if threat_score > 0.35:
                return "Non-Bailable (Organized Crime Embargo / Sec 111 BNS)"

        minor_codes = ["323", "504", "506", "379", "411", "317", "66"]
        if any(bool(re.search(rf'\b{code}\b', sec_str)) for code in minor_codes):
            return "Bailable (Statutory Right / Summons Triable)"

        return "Bailable (Judicial Discretion / Conditional Release)"

    def analyze_and_score(self) -> Dict[str, Any]:
        if len(self.graph.nodes) == 0:
            return {
                "nodes": [],
                "links": [],
                "stats": {
                    "total_entities": 0,
                    "total_connections": 0,
                    "detected_syndicates": 0,
                    "critical_threat_nodes": 0
                }
            }

        degree_cen = nx.degree_centrality(self.graph)
        between_cen = nx.betweenness_centrality(self.graph)
        try:
            pagerank_cen = nx.pagerank(self.graph, alpha=0.85, weight="weight")
        except Exception:
            pagerank_cen = degree_cen

        try:
            partition = community_louvain.best_partition(self.graph)
        except Exception:
            partition = {n: 0 for n in self.graph.nodes}

        suspect_nodes = [
            n for n, d in self.graph.nodes(data=True)
            if d.get("type") == "PERSON" and not d.get("details", {}).get("is_alias", False)
        ]
        total_suspects_count = len(suspect_nodes)

        total_cluster_flow = sum(
            float(d.get("amount", d.get("call_count", 1))) * 25000.0
            for _, _, d in self.graph.edges(data=True)
            if "FINANCIAL" in str(d.get("relationship", ""))
        ) or 750000.0

        human_threats: Dict[str, float] = {}
        human_roles: Dict[str, str] = {}
        human_bail: Dict[str, str] = {}
        human_hierarchy: Dict[str, str] = {}
        human_colors: Dict[str, str] = {}
        human_size_boosts: Dict[str, float] = {}
        critical_threat_count = 0

        for n_id in suspect_nodes:
            data = self.graph.nodes[n_id]
            b_score = float(between_cen.get(n_id, 0.0))
            p_score = float(pagerank_cen.get(n_id, 0.0))
            d_score = float(degree_cen.get(n_id, 0.0))
            degree_val = int(self.graph.degree(n_id))
            sections = data.get("details", {}).get("sections", [])
            sec_str = " ".join([str(s) for s in sections])

            class_info = self.classify_command_hierarchy(
                n_id=n_id,
                data=data,
                degree=degree_val,
                betweenness=b_score,
                pagerank=p_score,
                total_suspects=total_suspects_count
            )

            hierarchy_class = class_info["hierarchy_class"]

            ml_features = {
                "network_degree": degree_val,
                "network_betweenness": b_score,
                "topological_kingpin_score": p_score,
                "organized_operation_indicator": 1 if hierarchy_class in ["ACTUAL_KINGPIN", "APPARENT_KINGPIN"] else 0,
                "property_offence_indicator": 1 if any(s in sec_str for s in ["392", "379", "411", "317", "111"]) else 0,
                "ipc_392": 1 if "392" in sec_str else 0,
                "ipc_379": 1 if "379" in sec_str else 0,
                "ipc_411": 1 if ("411" in sec_str or "317" in sec_str) else 0,
                "physical_force_used": 1 if any(s in sec_str for s in ["103", "302", "307", "Arms", "25"]) else 0,
                "court_level_High Court": 1,
                "case_type_Writ Petition (Detention)": 0,
                "number_of_accused": max(1, total_suspects_count),
                "unauthorized_transfer_amount_inr": total_cluster_flow * (p_score + 0.15) if hierarchy_class == "ACTUAL_KINGPIN" else 0.0
            }

            try:
                if self.ml_service:
                    ml_intel = self.ml_service.predict_entity_intelligence(ml_features)
                    raw_threat = float(ml_intel["ml_syndicate_probability"])
                    role_title = class_info["ml_role"]
                else:
                    raise Exception("ML Engine Offline")
            except Exception:
                raw_threat = round(min(0.95, (p_score * 3.2) + (b_score * 1.8) + class_info["threat_bias"] * 0.35), 3)
                role_title = class_info["ml_role"]

            if hierarchy_class == "ACTUAL_KINGPIN":
                raw_threat = max(0.85, raw_threat)
            elif hierarchy_class == "APPARENT_KINGPIN":
                raw_threat = max(0.70, raw_threat)

            if raw_threat >= 0.70:
                critical_threat_count += 1

            human_threats[n_id] = raw_threat
            human_roles[n_id] = role_title
            human_hierarchy[n_id] = hierarchy_class
            human_colors[n_id] = class_info["color"]
            human_size_boosts[n_id] = class_info["size_boost"]
            human_bail[n_id] = self.determine_statutory_bail(
                sections=sections,
                hierarchy_class=hierarchy_class,
                suspect_role=role_title,
                threat_score=raw_threat
            )

        peripheral_threats = self._propagate_peripheral_threat(human_threats)

        formatted_nodes = []
        for n_id, data in self.graph.nodes(data=True):
            node_type = data.get("type", "PERSON")
            is_alias = data.get("details", {}).get("is_alias", False)
            b_score = float(between_cen.get(n_id, 0.0))
            p_score = float(pagerank_cen.get(n_id, 0.0))
            d_score = float(degree_cen.get(n_id, 0.0))
            degree_val = int(self.graph.degree(n_id))

            if node_type == "PERSON" and not is_alias:
                composite_risk = human_threats.get(n_id, 0.20)
                ml_role = human_roles.get(n_id, "Suspect")
                bail = human_bail.get(n_id, "Bailable")
                color = human_colors.get(n_id, "#a855f7")
                size_boost = human_size_boosts.get(n_id, 0.0)
                conviction = f"{composite_risk * 90:.1f}%"
            else:
                composite_risk = peripheral_threats.get(n_id, data.get("risk_score", 0.15))
                ml_role = "Alias Moniker" if is_alias else None
                bail = "N/A"
                conviction = "N/A"
                size_boost = 0.0
                
                # --- FIXED COLOR MAPPINGS TO MATCH LEGEND ---
                if is_alias:
                    color = "#ec4899"
                elif node_type == "CRIME_FIR":
                    color = "#f43f5e"     # Crime FIR Cases -> Rose (#f43f5e)
                elif node_type == "POLICE_STATION":
                    color = "#14b8a6"     # Police Station / Jurisdiction -> Teal
                elif node_type == "PHONE":
                    color = "#06b6d4"     # Surveillance Target / Phone -> Cyan (#06b6d4)
                elif node_type == "BANK_ACCOUNT":
                    color = "#10b981"     # Mule Bank Accounts -> Emerald (#10b981)
                elif node_type == "VEHICLE":
                    color = "#6366f1"     # Logistics Assets -> Indigo (#6366f1)
                elif node_type == "WEAPON":
                    color = "#f97316"     # Weapons / Contraband -> Orange (#f97316)
                else:
                    color = "#94a3b8"

            base_size = 9.0 + (p_score * 45.0) + min(10.0, degree_val * 1.6) + size_boost

            formatted_nodes.append({
                "id": n_id,
                "name": data.get("name", n_id),
                "type": node_type,
                "risk_score": composite_risk,
                "color": color,
                "size": round(base_size, 1),
                "cluster": f"Syndicate-{partition.get(n_id, 0) + 1}",
                "details": {
                    **data.get("details", {}),
                    "betweenness": round(b_score, 4),
                    "pagerank": round(p_score, 4),
                    "degree": round(d_score, 4),
                    "ml_role": ml_role,
                    "conviction_propensity": conviction,
                    "bail_eligibility": bail
                }
            })

        formatted_links = []
        for u, v, link_data in self.graph.edges(data=True):
            formatted_links.append({
                "source": u,
                "target": v,
                "relationship": link_data.get("relationship", "ASSOCIATED_WITH"),
                "label": link_data.get("label", "CONNECTED"),
                "weight": float(link_data.get("weight", 1.0)),
                "call_count": int(link_data.get("call_count", 1)),
                "timestamp": link_data.get("timestamp", "")
            })

        return {
            "nodes": formatted_nodes,
            "links": formatted_links,
            "stats": {
                "total_entities": len(formatted_nodes),
                "total_connections": len(formatted_links),
                "detected_syndicates": len(set(partition.values())) if partition else 0,
                "critical_threat_nodes": critical_threat_count
            }
        }