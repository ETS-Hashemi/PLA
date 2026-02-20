import networkx as nx
import matplotlib.pyplot as plt

def visualize_reasoning(facts, rules, explanations, output_file="reasoning_graph.png"):
    """Visualize the reasoning process as a directed graph."""
    graph = nx.DiGraph()

    # Add facts as nodes
    for fact in facts:
        graph.add_node(fact, color="green")

    # Add rules and explanations as edges
    for explanation in explanations:
        parts = explanation.split(" triggered ")
        if len(parts) == 2:
            conditions, result = parts
            for condition in conditions.split(" and "):
                graph.add_edge(condition.strip(), result.strip())

    # Draw the graph
    pos = nx.spring_layout(graph)
    colors = [graph.nodes[node].get("color", "blue") for node in graph.nodes]
    nx.draw(graph, pos, with_labels=True, node_color=colors, node_size=2000, font_size=10)
    plt.savefig(output_file)
    plt.show()
