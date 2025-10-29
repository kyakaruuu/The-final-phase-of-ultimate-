"""
Knowledge Graph Reasoning
Bot understands relationships between concepts, makes inferences
Impact: MASSIVE | Effort: 7 days
"""

import logging
import networkx as nx
from typing import Dict, List, Set, Tuple
import json

logger = logging.getLogger(__name__)

class ChemistryKnowledgeGraph:
    """
    Represents chemistry concepts as a knowledge graph
    Enables reasoning about concept relationships
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_chemistry_knowledge_graph()
    
    def _build_chemistry_knowledge_graph(self):
        """Build the core chemistry knowledge graph"""
        # Fundamental concepts
        self.graph.add_node("organic_chemistry", type="domain")
        self.graph.add_node("reaction_mechanisms", type="category")
        self.graph.add_node("stereochemistry", type="category")
        self.graph.add_node("electronic_effects", type="category")
        
        # SN1 knowledge
        self.graph.add_node("SN1", type="mechanism")
        self.graph.add_edge("reaction_mechanisms", "SN1", relationship="contains")
        self.graph.add_node("carbocation", type="intermediate")
        self.graph.add_edge("SN1", "carbocation", relationship="forms")
        self.graph.add_node("racemization", type="outcome")
        self.graph.add_edge("SN1", "racemization", relationship="produces")
        self.graph.add_node("carbocation_stability", type="concept")
        self.graph.add_edge("carbocation", "carbocation_stability", relationship="depends_on")
        
        # SN2 knowledge  
        self.graph.add_node("SN2", type="mechanism")
        self.graph.add_edge("reaction_mechanisms", "SN2", relationship="contains")
        self.graph.add_node("backside_attack", type="process")
        self.graph.add_edge("SN2", "backside_attack", relationship="requires")
        self.graph.add_node("inversion", type="outcome")
        self.graph.add_edge("SN2", "inversion", relationship="produces")
        self.graph.add_node("steric_hindrance", type="factor")
        self.graph.add_edge("steric_hindrance", "SN2", relationship="inhibits")
        
        # NGP knowledge
        self.graph.add_node("NGP", type="mechanism")
        self.graph.add_edge("reaction_mechanisms", "NGP", relationship="contains")
        self.graph.add_node("neighboring_group", type="structural_feature")
        self.graph.add_edge("NGP", "neighboring_group", relationship="requires")
        self.graph.add_node("rate_enhancement", type="effect")
        self.graph.add_edge("NGP", "rate_enhancement", relationship="causes")
        self.graph.add_edge("neighboring_group", "carbocation", relationship="stabilizes")
        
        # E1/E2 knowledge
        self.graph.add_node("E1", type="mechanism")
        self.graph.add_node("E2", type="mechanism")
        self.graph.add_edge("reaction_mechanisms", "E1", relationship="contains")
        self.graph.add_edge("reaction_mechanisms", "E2", relationship="contains")
        self.graph.add_edge("E1", "carbocation", relationship="forms")
        self.graph.add_node("Zaitsev_rule", type="principle")
        self.graph.add_node("Hofmann_rule", type="principle")
        self.graph.add_edge("E1", "Zaitsev_rule", relationship="follows")
        self.graph.add_edge("E2", "Zaitsev_rule", relationship="usually_follows")
        self.graph.add_node("anti_periplanar", type="requirement")
        self.graph.add_edge("E2", "anti_periplanar", relationship="requires")
        
        # Competition relationships
        self.graph.add_edge("SN1", "E1", relationship="competes_with")
        self.graph.add_edge("SN2", "E2", relationship="competes_with")
        
        # Prerequisites
        self.graph.add_edge("carbocation_stability", "SN1", relationship="prerequisite_for")
        self.graph.add_edge("stereochemistry", "SN2", relationship="prerequisite_for")
        
        logger.info(f"Knowledge graph built with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
    
    def find_prerequisite_concepts(self, concept: str) -> List[str]:
        """Find what concepts student needs to know before learning this one"""
        if concept not in self.graph:
            return []
        
        prerequisites = []
        for pred in self.graph.predecessors(concept):
            edge_data = self.graph.get_edge_data(pred, concept)
            if edge_data and edge_data.get("relationship") == "prerequisite_for":
                prerequisites.append(pred)
        
        return prerequisites
    
    def find_related_concepts(self, concept: str, max_distance: int = 2) -> List[Tuple[str, int]]:
        """Find concepts related to this one within max_distance hops"""
        if concept not in self.graph:
            return []
        
        related = []
        
        # Use BFS to find concepts within max_distance
        try:
            shortest_paths = nx.single_source_shortest_path_length(
                self.graph.to_undirected(), concept, cutoff=max_distance
            )
            
            for node, distance in shortest_paths.items():
                if node != concept and distance > 0:
                    related.append((node, distance))
            
            # Sort by distance
            related.sort(key=lambda x: x[1])
        except Exception as e:
            logger.error(f"Error finding related concepts: {e}")
        
        return related
    
    def explain_concept_relationship(self, concept1: str, concept2: str) -> str:
        """Explain how two concepts are related"""
        if concept1 not in self.graph or concept2 not in self.graph:
            return "Concepts not found in knowledge base."
        
        try:
            # Find shortest path
            path = nx.shortest_path(self.graph.to_undirected(), concept1, concept2)
            
            if len(path) == 2:
                # Direct connection
                edge_data = self.graph.get_edge_data(concept1, concept2) or self.graph.get_edge_data(concept2, concept1)
                relationship = edge_data.get("relationship", "related to") if edge_data else "related to"
                return f"{concept1} is {relationship} {concept2}"
            else:
                # Multi-hop connection
                explanation = f"{concept1} connects to {concept2} through: "
                explanation += " → ".join(path)
                return explanation
        except nx.NetworkXNoPath:
            return f"{concept1} and {concept2} are not directly connected in the knowledge graph."
        except Exception as e:
            logger.error(f"Error explaining relationship: {e}")
            return "Unable to determine relationship."
    
    def recommend_learning_path(self, target_concept: str) -> List[str]:
        """Recommend order to learn concepts to reach target"""
        if target_concept not in self.graph:
            return []
        
        # Find all prerequisites recursively
        learning_path = []
        visited = set()
        
        def find_prerequisites_recursive(concept):
            if concept in visited:
                return
            visited.add(concept)
            
            prereqs = self.find_prerequisite_concepts(concept)
            for prereq in prereqs:
                find_prerequisites_recursive(prereq)
            
            if concept not in learning_path:
                learning_path.append(concept)
        
        find_prerequisites_recursive(target_concept)
        
        return learning_path
    
    def infer_mechanism(self, substrate_features: Dict, reaction_conditions: Dict) -> str:
        """Use knowledge graph to infer likely mechanism"""
        # Analyze substrate features
        has_good_leaving_group = substrate_features.get("leaving_group_quality", "poor") in ["good", "excellent"]
        substrate_type = substrate_features.get("carbon_type", "primary")  # primary, secondary, tertiary
        has_neighboring_group = substrate_features.get("neighboring_group", False)
        
        # Analyze conditions
        nucleophile_strength = reaction_conditions.get("nucleophile_strength", "weak")
        is_polar_protic = reaction_conditions.get("solvent", "polar_aprotic") == "polar_protic"
        temperature = reaction_conditions.get("temperature", "room")
        base_strength = reaction_conditions.get("base_strength", "weak")
        
        # Inference logic using knowledge graph
        if has_neighboring_group:
            return "NGP - The neighboring group will participate and accelerate the reaction"
        
        if substrate_type == "tertiary":
            if is_polar_protic and has_good_leaving_group:
                if base_strength == "strong":
                    return "E1 likely - strong base + polar protic solvent + tertiary substrate"
                return "SN1 likely - polar protic solvent + tertiary carbocation is stable"
            elif nucleophile_strength == "strong":
                return "E2 likely - strong nucleophile can act as base on tertiary substrate"
        
        if substrate_type == "primary":
            if nucleophile_strength in ["strong", "moderate"]:
                return "SN2 likely - primary substrate + good nucleophile + little steric hindrance"
            elif base_strength == "strong":
                return "E2 likely - strong base on primary substrate"
        
        if substrate_type == "secondary":
            return "Mixed mechanisms possible - SN2/E2 or SN1/E1 depending on exact conditions. Need more info."
        
        return "Unable to determine mechanism with certainty - need more information"
    
    def visualize_concept_neighborhood(self, concept: str, depth: int = 2) -> Dict:
        """Get data to visualize concept and its neighborhood"""
        if concept not in self.graph:
            return {}
        
        # Get subgraph around concept
        nodes_to_include = {concept}
        related = self.find_related_concepts(concept, max_distance=depth)
        for node, dist in related:
            nodes_to_include.add(node)
        
        subgraph = self.graph.subgraph(nodes_to_include)
        
        # Convert to JSON-serializable format
        viz_data = {
            "nodes": [
                {
                    "id": node,
                    "type": subgraph.nodes[node].get("type", "concept"),
                    "is_center": node == concept
                }
                for node in subgraph.nodes()
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "relationship": data.get("relationship", "related")
                }
                for u, v, data in subgraph.edges(data=True)
            ]
        }
        
        return viz_data
