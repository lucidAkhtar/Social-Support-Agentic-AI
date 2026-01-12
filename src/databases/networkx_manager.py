"""
NetworkX Manager - In-Memory Graph Database (Neo4j Replacement)
Stores relationships: family trees, document connections, program matching

Benefits over Neo4j for Macbook M1 8GB RAM:
- 50 MB memory footprint vs 1200 MB
- No separate server process
- Fast in-memory graph operations
- Export to Neo4j later if needed
"""

import networkx as nx
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class NetworkXManager:
    """
    In-memory graph database using NetworkX.
    Replaces Neo4j with minimal memory footprint.
    """
    
    def __init__(self, persist_path: str = "data/databases/networkx"):
        self.persist_path = Path(persist_path)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        
        # Create directed graph for application flows
        self.graph = nx.DiGraph()
        
        # Node type prefixes for easy identification
        self.NODE_TYPES = {
            'application': 'APP',
            'person': 'PERSON',
            'document': 'DOC',
            'program': 'PROG',
            'decision': 'DEC',
            'family': 'FAMILY'
        }
        
        # Initialize with enablement programs
        self._initialize_programs()
        
        logger.info("NetworkX graph database initialized")
    
    def _initialize_programs(self):
        """Initialize enablement programs as nodes"""
        programs = [
            {
                'name': 'UAE Job Placement Service',
                'category': 'Employment',
                'description': 'Connect job seekers with employment opportunities',
                'target_audience': ['unemployed', 'low_income'],
                'duration': '3-6 months',
                'priority': 'high'
            },
            {
                'name': 'Professional Skills Bootcamp',
                'category': 'Skills Training',
                'description': 'Intensive training in high-demand skills',
                'target_audience': ['low_experience', 'career_change'],
                'duration': '12 weeks',
                'priority': 'high'
            },
            {
                'name': 'Career Development Counseling',
                'category': 'Career Guidance',
                'description': 'One-on-one career counseling and planning',
                'target_audience': ['all'],
                'duration': '6 months',
                'priority': 'medium'
            },
            {
                'name': 'Financial Wellness Program',
                'category': 'Financial Management',
                'description': 'Budgeting, debt management, and financial planning',
                'target_audience': ['financial_stress', 'high_debt'],
                'duration': '6 months',
                'priority': 'high'
            },
            {
                'name': 'Small Business Development',
                'category': 'Entrepreneurship',
                'description': 'Support for starting and growing businesses',
                'target_audience': ['entrepreneurial', 'business_owner'],
                'duration': '12 months',
                'priority': 'medium'
            },
            {
                'name': 'Higher Education Scholarship',
                'category': 'Education',
                'description': 'Financial support for higher education',
                'target_audience': ['young', 'low_education'],
                'duration': '2-4 years',
                'priority': 'medium'
            },
            {
                'name': 'Wellbeing & Resilience Support',
                'category': 'Mental Health',
                'description': 'Counseling and mental health support',
                'target_audience': ['high_stress', 'family_issues'],
                'duration': '6-12 months',
                'priority': 'high'
            }
        ]
        
        for program in programs:
            node_id = f"PROG_{program['name'].replace(' ', '_')}"
            self.graph.add_node(node_id, node_type='program', **program)
    
    # ========== Node Creation ==========
    
    def create_application_node(self, application_id: str, applicant_name: str,
                               profile_data: Dict[str, Any]) -> str:
        """Create application node"""
        node_id = f"APP_{application_id}"
        
        self.graph.add_node(
            node_id,
            node_type='application',
            application_id=application_id,
            applicant_name=applicant_name,
            created_at=datetime.now().isoformat(),
            status='pending',
            **profile_data
        )
        
        # Create person node and link
        person_id = self._create_person_node(applicant_name, profile_data)
        self.graph.add_edge(person_id, node_id, relationship='APPLIED_FOR')
        
        logger.info(f"Created application node: {node_id}")
        return node_id
    
    def _create_person_node(self, name: str, profile_data: Dict[str, Any]) -> str:
        """Create person node"""
        id_number = profile_data.get('id_number', 'unknown')
        node_id = f"PERSON_{id_number}"
        
        if node_id not in self.graph:
            self.graph.add_node(
                node_id,
                node_type='person',
                name=name,
                id_number=id_number,
                monthly_income=profile_data.get('monthly_income', 0),
                employment_status=profile_data.get('employment_status', 'unknown'),
                family_size=profile_data.get('family_size', 1)
            )
        
        return node_id
    
    def add_document_node(self, application_id: str, document_id: str,
                         document_type: str, extracted_data: Dict[str, Any]) -> str:
        """Add document node and link to application"""
        app_node = f"APP_{application_id}"
        doc_node = f"DOC_{document_id}"
        
        self.graph.add_node(
            doc_node,
            node_type='document',
            document_id=document_id,
            document_type=document_type,
            uploaded_at=datetime.now().isoformat(),
            **extracted_data
        )
        
        self.graph.add_edge(app_node, doc_node, relationship='HAS_DOCUMENT')
        
        logger.info(f"Added document node: {doc_node}")
        return doc_node
    
    def create_decision_node(self, application_id: str, decision_data: Dict[str, Any]) -> str:
        """Create decision node"""
        app_node = f"APP_{application_id}"
        dec_node = f"DEC_{application_id}"
        
        # Extract specific fields to avoid duplicates
        node_attrs = {
            'node_type': 'decision',
            'decision_type': decision_data.get('decision_type', 'unknown'),
            'eligibility_score': decision_data.get('eligibility_score', 0.0),
            'is_eligible': decision_data.get('is_eligible', False),
            'ml_prediction': decision_data.get('ml_prediction', 0.0),
            'policy_rules_met': decision_data.get('policy_rules_met', 0),
            'final_decision': decision_data.get('final_decision', 'unknown'),
            'decided_at': datetime.now().isoformat()
        }
        
        self.graph.add_node(dec_node, **node_attrs)
        self.graph.add_edge(app_node, dec_node, relationship='RESULTED_IN')
        
        logger.info(f"Created decision node: {dec_node}")
        return dec_node
    
    # ========== Relationship Creation ==========
    
    def link_to_programs(self, application_id: str, program_names: List[str]) -> None:
        """Link application to recommended programs"""
        dec_node = f"DEC_{application_id}"
        
        for program_name in program_names:
            prog_node = f"PROG_{program_name.replace(' ', '_')}"
            if prog_node in self.graph:
                self.graph.add_edge(
                    dec_node, prog_node, 
                    relationship='RECOMMENDED',
                    recommended_at=datetime.now().isoformat()
                )
        
        logger.info(f"Linked {len(program_names)} programs to {application_id}")
    
    def create_validation_relationship(self, application_id: str, 
                                      validation_data: Dict[str, Any]) -> None:
        """Create validation relationships between documents"""
        app_node = f"APP_{application_id}"
        
        # Get all document nodes for this application
        doc_nodes = [
            n for n, d in self.graph.nodes(data=True)
            if d.get('node_type') == 'document' and 
               self.graph.has_edge(app_node, n)
        ]
        
        # Create consistency edges between documents
        for i, doc1 in enumerate(doc_nodes):
            for doc2 in doc_nodes[i+1:]:
                self.graph.add_edge(
                    doc1, doc2,
                    relationship='CROSS_VALIDATED',
                    is_consistent=validation_data.get('is_valid', False),
                    validated_at=datetime.now().isoformat()
                )
    
    def add_family_relationship(self, person1_id: str, person2_id: str, 
                               relationship_type: str) -> None:
        """Add family relationships"""
        p1_node = f"PERSON_{person1_id}"
        p2_node = f"PERSON_{person2_id}"
        
        self.graph.add_edge(p1_node, p2_node, relationship=relationship_type)
        logger.info(f"Added family relationship: {relationship_type}")
    
    # ========== Graph Queries ==========
    
    def get_application_graph(self, application_id: str) -> Dict[str, Any]:
        """Get complete graph for an application"""
        app_node = f"APP_{application_id}"
        
        if app_node not in self.graph:
            return None
        
        # Get all connected nodes (BFS)
        connected_nodes = nx.descendants(self.graph, app_node)
        connected_nodes.add(app_node)
        
        # Get subgraph
        subgraph = self.graph.subgraph(connected_nodes)
        
        return {
            'nodes': [
                {'id': n, **self.graph.nodes[n]}
                for n in subgraph.nodes()
            ],
            'edges': [
                {
                    'source': u,
                    'target': v,
                    **self.graph.edges[u, v]
                }
                for u, v in subgraph.edges()
            ]
        }
    
    def get_recommended_programs(self, application_id: str) -> List[Dict[str, Any]]:
        """Get programs recommended for an application"""
        dec_node = f"DEC_{application_id}"
        
        if dec_node not in self.graph:
            return []
        
        programs = []
        for neighbor in self.graph.successors(dec_node):
            if self.graph.nodes[neighbor].get('node_type') == 'program':
                programs.append(dict(self.graph.nodes[neighbor]))
        
        return programs
    
    def get_similar_applications(self, application_id: str, limit: int = 5) -> List[str]:
        """Find similar applications based on graph structure"""
        app_node = f"APP_{application_id}"
        
        # Get application profile - either from graph or database
        if app_node in self.graph:
            app_data = self.graph.nodes[app_node]
            target_income = app_data.get('monthly_income', 0)
            target_status = app_data.get('employment_status', '')
        else:
            # Application not in graph yet - fetch from database for comparison
            try:
                import sqlite3
                conn = sqlite3.connect('data/databases/applications.db')
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT monthly_income, employment_status 
                    FROM applications 
                    WHERE app_id = ?
                """, (application_id,))
                row = cursor.fetchone()
                conn.close()
                
                if not row:
                    return []
                
                target_income = float(row['monthly_income']) if row['monthly_income'] else 0
                target_status = row['employment_status'] or ''
            except Exception as e:
                logger.warning(f"Failed to get application data from database: {e}")
                return []
        
        # Find similar applications in graph
        similar_apps = []
        for node, data in self.graph.nodes(data=True):
            if data.get('node_type') == 'application' and node != app_node:
                income_diff = abs(data.get('monthly_income', 0) - target_income)
                if income_diff < 2000 and data.get('employment_status') == target_status:
                    similar_apps.append(node.replace('APP_', ''))
        
        return similar_apps[:limit]
    
    def find_related_applications(self, person_id: str) -> List[Dict[str, Any]]:
        """Find applications related to a person (alias for compatibility)"""
        person_node = f"PERSON_{person_id}"
        
        if person_node not in self.graph:
            return []
        
        # Find applications connected to this person
        related_apps = []
        for neighbor in self.graph.neighbors(person_node):
            if self.graph.nodes[neighbor].get('node_type') == 'application':
                app_data = dict(self.graph.nodes[neighbor])
                app_data['application_id'] = neighbor.replace('APP_', '')
                related_apps.append(app_data)
        
        return related_apps
    
    def trace_decision_path(self, application_id: str) -> List[Dict[str, Any]]:
        """Trace the decision path for an application"""
        app_node = f"APP_{application_id}"
        
        if app_node not in self.graph:
            return []
        
        # Find path from app to decision node
        dec_node = f"DEC_{application_id}"
        
        if dec_node not in self.graph:
            return []
        
        try:
            path = nx.shortest_path(self.graph, app_node, dec_node)
            path_data = []
            
            for node in path:
                node_data = dict(self.graph.nodes[node])
                node_data['node_id'] = node
                path_data.append(node_data)
            
            return path_data
        except nx.NetworkXNoPath:
            return []
    
    def get_document_consistency(self, application_id: str) -> Dict[str, Any]:
        """Check document consistency relationships"""
        app_node = f"APP_{application_id}"
        
        doc_nodes = [
            n for n, d in self.graph.nodes(data=True)
            if d.get('node_type') == 'document' and 
               self.graph.has_edge(app_node, n)
        ]
        
        total_pairs = 0
        consistent_pairs = 0
        
        for i, doc1 in enumerate(doc_nodes):
            for doc2 in doc_nodes[i+1:]:
                if self.graph.has_edge(doc1, doc2):
                    total_pairs += 1
                    edge_data = self.graph.edges[doc1, doc2]
                    if edge_data.get('is_consistent', False):
                        consistent_pairs += 1
        
        return {
            'total_documents': len(doc_nodes),
            'total_comparisons': total_pairs,
            'consistent_pairs': consistent_pairs,
            'consistency_rate': consistent_pairs / total_pairs if total_pairs > 0 else 0.0
        }
    
    def get_program_recommendations_graph(self, profile_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get program recommendations based on profile"""
        matching_programs = []
        
        for node, data in self.graph.nodes(data=True):
            if data.get('node_type') == 'program':
                target_audience = data.get('target_audience', [])
                
                # Match based on criteria
                if 'unemployed' in target_audience and profile_criteria.get('employment_status') == 'unemployed':
                    matching_programs.append(dict(data))
                elif 'low_income' in target_audience and profile_criteria.get('monthly_income', 0) < 3000:
                    matching_programs.append(dict(data))
                elif 'all' in target_audience:
                    matching_programs.append(dict(data))
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        matching_programs.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 3))
        
        return matching_programs
    
    # ========== Graph Statistics ==========
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        node_types = {}
        for node, data in self.graph.nodes(data=True):
            node_type = data.get('node_type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'node_types': node_types,
            'is_directed': self.graph.is_directed(),
            'is_connected': nx.is_weakly_connected(self.graph) if self.graph.number_of_nodes() > 0 else False
        }
    
    # ========== Persistence ==========
    
    def save_graph(self, filename: str = "application_graph.json") -> None:
        """Save graph to JSON file"""
        file_path = self.persist_path / filename
        
        # Convert to node-link format
        data = nx.node_link_data(self.graph)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Graph saved to {file_path}")
    
    def load_graph(self, filename: str = "application_graph.json") -> bool:
        """Load graph from JSON file"""
        file_path = self.persist_path / filename
        
        if not file_path.exists():
            # Fresh system - graph will be saved after first application
            logger.debug(f"Graph file not found: {file_path} - will be created on first save")
            return False
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            self.graph = nx.node_link_graph(data, directed=True)
            logger.info(f"Graph loaded from {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load graph: {e}")
            return False
    
    def export_to_cypher(self, filename: str = "neo4j_import.cypher") -> None:
        """Export graph as Neo4j Cypher queries for future migration"""
        file_path = self.persist_path / filename
        
        with open(file_path, 'w') as f:
            # Create nodes
            for node, data in self.graph.nodes(data=True):
                node_type = data.get('node_type', 'Unknown').title()
                props = {k: v for k, v in data.items() if k != 'node_type'}
                props_str = ', '.join([f"{k}: '{v}'" if isinstance(v, str) else f"{k}: {v}" 
                                      for k, v in props.items()])
                f.write(f"CREATE (n:{node_type} {{{props_str}}});\n")
            
            # Create relationships
            for u, v, data in self.graph.edges(data=True):
                rel_type = data.get('relationship', 'RELATED_TO')
                props = {k: v for k, v in data.items() if k != 'relationship'}
                props_str = ', '.join([f"{k}: '{v}'" if isinstance(v, str) else f"{k}: {v}" 
                                      for k, v in props.items()])
                f.write(f"MATCH (a), (b) WHERE a.id = '{u}' AND b.id = '{v}' ")
                f.write(f"CREATE (a)-[:{rel_type} {{{props_str}}}]->(b);\n")
        
        logger.info(f"Cypher export saved to {file_path}")
