# Copyright 2023 Brit Group Services Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
    """build from hades's event_results object the full set of connections as a networkx digraph"""
    if allowed_responses is None:
        allowed_responses = {NotificationResponse.ACK}
    graph = MultiDiGraph()
    added_edges: set[tuple[str, str, str]] = set()
    for (event, source_process_name, source_process_instance_id, _), event_notifications in sorted(
        underworld.event_results.items(), key=lambda x: x[0][0].t
    ):
        source_node = f"{source_process_name} - {source_process_instance_id}"
        graph.add_node(source_node)
        for (target_process_name, target_process_instance_id), notification_response in event_notifications.items():
            target_node = f"{target_process_name} - {target_process_instance_id}"
            graph.add_node(target_node)
            if notification_response in allowed_responses and (source_node, target_node, event.name) not in added_edges:
                graph.add_edge(source_node, target_node, label=event.name)
                added_edges.add((source_node, target_node, event.name))
    return graph
