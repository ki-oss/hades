from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from networkx.classes.digraph import MultiDiGraph
else:
    from networkx import MultiDiGraph

from hades import Hades, NotificationResponse


def write_mermaid(G: MultiDiGraph) -> str:
    """output a networkx digraph as a simple mermaid graph"""
    lines = []
    for u_node, v_node, edge in sorted(G.edges(data=True), key=lambda x: x[0] + x[1] + x[2]["label"]):
        lines.append(f"{u_node.replace(' ', '')}({u_node}) -- {edge['label']} --> {v_node.replace(' ', '')}({v_node})")
    mermaid_lines = "\n".join(lines)
    return f"graph LR\n{mermaid_lines}"


def to_digraph(underworld: Hades, allowed_responses: set[NotificationResponse] | None = None) -> MultiDiGraph:
    """return the full set of connections as a networkx digraph"""
    if allowed_responses is None:
        allowed_responses = {NotificationResponse.ACK}
    graph = MultiDiGraph()
    added_edges: set[tuple[str, str, str]] = set()
    for (
        event,
        source_process_name,
        source_process_instance_id,
    ), event_notifications in sorted(underworld.event_results.items(), key=lambda x: x[0][0].t):
        source_node = f"{source_process_name} - {source_process_instance_id}"
        graph.add_node(source_node)
        for (target_process_name, target_process_instance_id), notification_response in event_notifications.items():
            target_node = f"{target_process_name} - {target_process_instance_id}"
            graph.add_node(target_node)
            if notification_response in allowed_responses and (source_node, target_node, event.name) not in added_edges:
                graph.add_edge(source_node, target_node, label=event.name)
                added_edges.add((source_node, target_node, event.name))
    return graph
