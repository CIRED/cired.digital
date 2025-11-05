"""
Analyze visitor provenance for CIRED.digital.

This module classifies sessions by client IP (CIRED/RENATER/research,
French residential, bots, etc.) and renders a pie chart of visitors by
network origin.

Exports:
- classify_bot(ip): Identify an IP's origin/bot category.
- plot_visitors_origin_pie(sessions, save_path): Draw and optionally save the figure.

Usage:
    from logloader import sessions
    from fig_provenance import plot_visitors_origin_pie
    plot_visitors_origin_pie(sessions, "visitors_origin.png")
"""

from typing import Any

import matplotlib.pyplot as plt


def plot_visitors_origin_pie(
    sessions: list[dict[str, Any]], save_path: str | None = None
) -> None:
    """
    Create a pie chart showing visitors by network origin.

    Args:
        sessions: List of session dicts, each ideally with an "ip" key.
        save_path: Optional path to save the figure.

    """
    # Aggregate counts by label
    counts: dict[str, int] = {}
    for s in sessions:
        label = str(s.get("origin", "??"))
        counts[label] = counts.get(label, 0) + 1

    if not counts:
        print("No sessions to plot.")
        return

    labels = list(counts.keys())
    sizes = [counts[k] for k in labels]

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    ax.set_title(
        "CIRED.digital beta visitors by network origin",
        fontweight="bold",
        fontsize=14,
        pad=30,
    )

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    # Lazy import to avoid side effects on import
    from logloader import sessions as _sessions

    plot_visitors_origin_pie(_sessions, "visitors_origin.png")
