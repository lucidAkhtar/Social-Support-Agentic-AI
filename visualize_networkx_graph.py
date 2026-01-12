"""
NetworkX Graph Visualizer
Creates a visual representation of the knowledge graph for interviews
"""
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.patches as mpatches

def visualize_full_graph():
    """Visualize the entire graph"""
    graph_path = Path("application_graph.graphml")
    
    if not graph_path.exists():
        print("❌ Graph file not found: application_graph.graphml")
        return
    
    print("📊 Loading graph...")
    graph = nx.read_graphml(str(graph_path))
    
    print(f"📈 Visualizing {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges...")
    
    # Create layout
    pos = nx.spring_layout(graph, k=0.3, iterations=50, seed=42)
    
    # Color nodes by type
    node_colors = []
    node_labels = {}
    
    for node in graph.nodes():
        node_type = graph.nodes[node].get('node_type', 'unknown').lower()
        
        # Shortened labels for readability
        if node_type == 'application':
            node_colors.append('#3498db')  # Blue
            node_labels[node] = node.replace('APP_', '')[:10]
        elif node_type == 'decision':
            node_colors.append('#2ecc71')  # Green
            node_labels[node] = 'DEC'
        elif node_type == 'program':
            node_colors.append('#e74c3c')  # Red
            node_labels[node] = graph.nodes[node].get('name', '')[:15]
        elif node_type == 'document':
            node_colors.append('#f39c12')  # Orange
            node_labels[node] = 'DOC'
        elif node_type == 'person':
            node_colors.append('#9b59b6')  # Purple
            node_labels[node] = 'PERSON'
        else:
            node_colors.append('#95a5a6')  # Gray
            node_labels[node] = node[:10]
    
    # Create figure
    plt.figure(figsize=(20, 15))
    
    # Draw network
    nx.draw_networkx_nodes(
        graph, pos,
        node_color=node_colors,
        node_size=300,
        alpha=0.8
    )
    
    nx.draw_networkx_edges(
        graph, pos,
        edge_color='#bdc3c7',
        arrows=True,
        arrowsize=10,
        arrowstyle='->',
        alpha=0.5,
        width=0.5
    )
    
    nx.draw_networkx_labels(
        graph, pos,
        labels=node_labels,
        font_size=6,
        font_weight='bold'
    )
    
    # Legend
    legend_elements = [
        mpatches.Patch(facecolor='#3498db', label=f'Application ({sum(1 for n in graph.nodes() if graph.nodes[n].get("node_type", "").lower() == "application")} nodes)'),
        mpatches.Patch(facecolor='#2ecc71', label=f'Decision ({sum(1 for n in graph.nodes() if graph.nodes[n].get("node_type", "").lower() == "decision")} nodes)'),
        mpatches.Patch(facecolor='#e74c3c', label=f'Program ({sum(1 for n in graph.nodes() if graph.nodes[n].get("node_type", "").lower() == "program")} nodes)'),
        mpatches.Patch(facecolor='#f39c12', label=f'Document ({sum(1 for n in graph.nodes() if graph.nodes[n].get("node_type", "").lower() == "document")} nodes)'),
        mpatches.Patch(facecolor='#9b59b6', label=f'Person ({sum(1 for n in graph.nodes() if graph.nodes[n].get("node_type", "").lower() == "person")} nodes)')
    ]
    
    plt.legend(
        handles=legend_elements,
        loc='upper left',
        fontsize=12,
        framealpha=0.9
    )
    
    plt.title(
        f"Social Support Knowledge Graph\n{graph.number_of_nodes()} Nodes • {graph.number_of_edges()} Edges",
        fontsize=18,
        fontweight='bold',
        pad=20
    )
    
    plt.axis('off')
    plt.tight_layout()
    
    # Save with v2 suffix
    output_path = "networkx_graph_full_v2.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Full graph saved to: {output_path}")
    
    plt.close()


def visualize_single_application():
    """Visualize a single application's subgraph"""
    graph_path = Path("application_graph.graphml")
    
    if not graph_path.exists():
        print("❌ Graph file not found: application_graph.graphml")
        return
    
    print("📊 Loading graph...")
    graph = nx.read_graphml(str(graph_path))
    
    # Find first application node
    app_nodes = [n for n, d in graph.nodes(data=True) if d.get('node_type', '').lower() == 'application']
    
    if not app_nodes:
        print("❌ No application nodes found")
        return
    
    app_node = app_nodes[0]
    print(f"🔍 Visualizing application: {app_node}")
    
    # Get all connected nodes
    neighbors = set(nx.descendants(graph, app_node))
    neighbors.add(app_node)
    
    # Also get predecessors (person who applied)
    predecessors = set(nx.ancestors(graph, app_node))
    neighbors.update(predecessors)
    
    # Create subgraph
    subgraph = graph.subgraph(neighbors)
    
    print(f"📈 Subgraph: {subgraph.number_of_nodes()} nodes, {subgraph.number_of_edges()} edges")
    
    # Layout
    pos = nx.spring_layout(subgraph, k=1.5, iterations=100, seed=42)
    
    # Color nodes
    node_colors = []
    node_sizes = []
    node_labels = {}
    
    for node in subgraph.nodes():
        node_type = subgraph.nodes[node].get('node_type', 'unknown').lower()
        
        if node == app_node:
            # Highlight main application
            node_colors.append('#e74c3c')  # Red
            node_sizes.append(2000)
            node_labels[node] = f"{node}\n(Main)"
        elif node_type == 'application':
            node_colors.append('#3498db')  # Blue
            node_sizes.append(1500)
            node_labels[node] = node.replace('APP_', 'APP\n')
        elif node_type == 'decision':
            node_colors.append('#2ecc71')  # Green
            node_sizes.append(1500)
            decision_type = subgraph.nodes[node].get('decision_type', 'DEC')
            node_labels[node] = f"Decision\n{decision_type}"
        elif node_type == 'program':
            node_colors.append('#e67e22')  # Orange
            node_sizes.append(1200)
            prog_name = subgraph.nodes[node].get('name', 'Program')
            node_labels[node] = prog_name[:20]
        elif node_type == 'document':
            node_colors.append('#f39c12')  # Yellow
            node_sizes.append(1000)
            doc_type = subgraph.nodes[node].get('document_type', 'DOC')
            node_labels[node] = f"Doc:\n{doc_type}"
        elif node_type == 'person':
            node_colors.append('#9b59b6')  # Purple
            node_sizes.append(1500)
            person_name = subgraph.nodes[node].get('name', 'Person')
            node_labels[node] = f"Applicant:\n{person_name}"
        else:
            node_colors.append('#95a5a6')  # Gray
            node_sizes.append(1000)
            node_labels[node] = node[:15]
    
    # Create figure
    plt.figure(figsize=(16, 12))
    
    # Draw edges first
    nx.draw_networkx_edges(
        subgraph, pos,
        edge_color='#34495e',
        arrows=True,
        arrowsize=30,
        arrowstyle='->',
        alpha=0.6,
        width=2,
        connectionstyle='arc3,rad=0.1'
    )
    
    # Draw nodes
    nx.draw_networkx_nodes(
        subgraph, pos,
        node_color=node_colors,
        node_size=node_sizes,
        alpha=0.9,
        edgecolors='black',
        linewidths=2
    )
    
    # Draw labels
    nx.draw_networkx_labels(
        subgraph, pos,
        labels=node_labels,
        font_size=9,
        font_weight='bold',
        font_color='white'
    )
    
    # Edge labels (relationships)
    edge_labels = {}
    for u, v, data in subgraph.edges(data=True):
        rel = data.get('relationship', '')
        if rel:
            edge_labels[(u, v)] = rel
    
    nx.draw_networkx_edge_labels(
        subgraph, pos,
        edge_labels=edge_labels,
        font_size=7,
        font_color='#2c3e50',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7)
    )
    
    # Legend
    legend_elements = [
        mpatches.Patch(facecolor='#e74c3c', label='Main Application', edgecolor='black'),
        mpatches.Patch(facecolor='#9b59b6', label='Applicant (Person)', edgecolor='black'),
        mpatches.Patch(facecolor='#2ecc71', label='Decision', edgecolor='black'),
        mpatches.Patch(facecolor='#e67e22', label='Recommended Program', edgecolor='black'),
        mpatches.Patch(facecolor='#f39c12', label='Document', edgecolor='black')
    ]
    
    plt.legend(
        handles=legend_elements,
        loc='upper left',
        fontsize=11,
        framealpha=0.95
    )
    
    # Application details
    app_data = subgraph.nodes[app_node]
    details_text = f"Application Details:\n"
    details_text += f"ID: {app_node}\n"
    details_text += f"Name: {app_data.get('applicant_name', 'Unknown')}\n"
    details_text += f"Income: {app_data.get('monthly_income', 0)} AED\n"
    details_text += f"Family: {app_data.get('family_size', 0)} members\n"
    details_text += f"Status: {app_data.get('status', 'unknown')}"
    
    plt.text(
        0.02, 0.02,
        details_text,
        transform=plt.gca().transAxes,
        fontsize=10,
        verticalalignment='bottom',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9)
    )
    
    plt.title(
        f"Application Knowledge Graph: {app_node}\n{subgraph.number_of_nodes()} Connected Entities",
        fontsize=16,
        fontweight='bold',
        pad=20
    )
    
    plt.axis('off')
    plt.tight_layout()
    
    # Save with v2 suffix
    output_path = "networkx_graph_single_app_v2.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Application subgraph saved to: {output_path}")
    
    plt.close()


def main():
    print("="*60)
    print("  NetworkX Graph Visualizer")
    print("="*60)
    print()
    
    # Generate both visualizations
    visualize_full_graph()
    print()
    visualize_single_application()
    
    print()
    print("="*60)
    print("  Visualization Complete!")
    print("="*60)
    print()
    print("📁 Generated Files:")
    print("   1. networkx_graph_full_v2.png - Complete knowledge graph (latest data)")
    print("   2. networkx_graph_single_app_v2.png - Single application detail (latest data)")
    print()
    print("💡 These visualizations show:")
    print("   - Relationships between applicants, applications, decisions, programs")
    print("   - Graph structure for knowledge extraction")
    print("   - Program recommendation patterns")
    print()


if __name__ == "__main__":
    main()
