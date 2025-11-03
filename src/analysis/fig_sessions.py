"""
Session visualizations.

    Plot a network of all sessions showing event type transitions.

Minh Ha-Duong, CNRS, 2025-11
"""

from typing import Any

import matplotlib.pyplot as plt
import networkx as nx
from logloader import sessions  # Import sessions from logloader module


def plot_session_event_type_transitions(
    sessions: list[dict[str, Any]], save_path: str | None = None
) -> None:
    """Build a directed graph of event type transitions."""
    G = nx.DiGraph()

    # Track total events per node
    event_counts: dict[str, int] = {}

    for session in sessions:
        events = session["events"]

        # Count all events
        for event in events:
            event_type = event["eventType"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        # Build transition edges
        for i in range(len(events) - 1):
            src = events[i]["eventType"]
            dst = events[i + 1]["eventType"]
            if G.has_edge(src, dst):
                G[src][dst]["weight"] += 1
            else:
                G.add_edge(src, dst, weight=1)

        # Add edge from last event to sessionEnd
        if events:
            last_event = events[-1]["eventType"]
            if G.has_edge(last_event, "End"):
                G[last_event]["End"]["weight"] += 1
            else:
                G.add_edge(last_event, "End", weight=1)
            event_counts["End"] = event_counts.get("End", 0) + 1
    # Draw the graph
    plt.figure(figsize=(12, 8))

    pos = {
        "sessionStart": [0, 0.0],
        "Start": [0, 0.0],
        "request": [1, 0.0],
        "response": [2, 0.0],
        "article": [3, 0.0],
        "userInput": [1.5, 1.0],
        "btnClick": [1.5, 1.0],
        "userProfile": [0.5, 1.0],
        "feedback": [2.5, 1.0],
        "visibilityOn": [2.5, -1.0],
        "visible": [2.5, -1.0],
        "visibilityOff": [1.5, -1.0],
        "hidden": [1.5, -1.0],
        "End": [4, 0.0],
    }

    weights = [G[u][v]["weight"] for u, v in G.edges()]
    max_weight = max(weights) if weights else 1
    edge_widths = [3 * (w / max_weight) for w in weights]

    # Create labels with event counts
    labels = {node: f"{node}\n({event_counts.get(node, 0)})" for node in G.nodes()}

    nx.draw(
        G,
        pos,
        labels=labels,
        with_labels=True,
        node_size=4000,
        node_color="lightblue",
        arrowsize=20,
        connectionstyle="arc3,rad=0.2",
        width=edge_widths,
    )
    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels={(u, v): d["weight"] for u, v, d in G.edges(data=True)},
        connectionstyle="arc3,rad=0.2",
    )
    plt.title("CIRED.digital user journeys, beta phase (summer 2025)")
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()


def simplify(session: dict[str, Any]) -> dict[str, Any]:
    """Simplify session by dropping consecutive "visibilityOff, visibilityOn" events and the final visibilityOff."""
    simplified_events = []
    skip_next = False

    events = session["events"]
    for i, event in enumerate(events):
        if skip_next:
            skip_next = False
            continue

        # Skip only "visibilityOff" events that are immediately followed by "visibilityOn" events,
        if (
            event["eventType"] == "visibilityOff"
            and i + 1 < len(events)
            and events[i + 1]["eventType"] == "visibilityOn"
        ):
            skip_next = (
                True  # Skip both this "visibilityOff" and the next "visibilityOn" event
            )
            continue  # Skip this "visibilityOff" event

        # Relabel nodes
        if event["eventType"] == "userInput":
            event["eventType"] = "btnClick"
        if event["eventType"] == "sessionStart":
            event["eventType"] = "Start"
        if event["eventType"] == "visibilityOn":
            event["eventType"] = "visible"
        if event["eventType"] == "visibilityOff":
            event["eventType"] = "hidden"

        simplified_events.append(event)

    # Remove final "hidden" if it exists
    if simplified_events and simplified_events[-1]["eventType"] == "hidden":
        simplified_events.pop()

    session["events"] = simplified_events
    return session


if __name__ == "__main__":
    plot_session_event_type_transitions(sessions, "session_event_type_transitions.png")

    sessions = [simplify(session) for session in sessions]
    plot_session_event_type_transitions(
        sessions, "session_event_type_transitions_simplified.png"
    )
