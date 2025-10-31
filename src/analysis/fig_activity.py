"""
Plot Cired.digital activity timeline.

A dual-axis line chart shows the number of sessions and requests over time.
Shaded regions indicate different project phases (Alpha, Beta closed, Beta open).
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from logloader import events_df


def plot_session_activity_timeline(
    events_df: pd.DataFrame, save_path: str | None = None
) -> None:
    """
    Create a dual-axis line chart showing sessions and requests over time.

    Includes phase markers (Alpha, Beta closed, Beta open).
    """
    # Aggregate by date
    daily_stats = (
        events_df.groupby("date")
        .agg(
            sessions=("sessionId", "nunique"),
            requests=("query", "nunique"),
        )
        .reset_index()
    )
    daily_stats["date"] = pd.to_datetime(daily_stats["date"])

    # Create figure with dual axes
    _, ax1 = plt.subplots(figsize=(14, 6))

    # Plot sessions on left axis
    color1 = "#2E86AB"
    ax1.set_xlabel("Date", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Number of Sessions", color=color1, fontsize=12, fontweight="bold")
    ax1.margins(x=0)
    ax1.margins(y=0.1)
    line1 = ax1.plot(
        daily_stats["date"],
        daily_stats["sessions"],
        color=color1,
        linewidth=2.5,
        marker="o",
        markersize=6,
        label="Sessions",
    )
    ax1.tick_params(axis="y", labelcolor=color1)
    ax1.grid(True, alpha=0.3)

    # Plot requests on right axis
    ax2 = ax1.twinx()
    ax2.margins(x=0)
    ax2.margins(y=0.1)
    color2 = "#A23B72"
    ax2.set_ylabel("Number of Requests", color=color2, fontsize=12, fontweight="bold")
    line2 = ax2.plot(
        daily_stats["date"],
        daily_stats["requests"],
        color=color2,
        linewidth=2.5,
        marker="s",
        markersize=6,
        linestyle="--",
        label="Requests",
    )
    ax2.tick_params(axis="y", labelcolor=color2)

    # Lock scales
    ymin = min(ax1.get_ylim()[0], ax2.get_ylim()[0])
    ymax = max(ax1.get_ylim()[1], ax2.get_ylim()[1])
    ax1.set_ylim(ymin, ymax)
    ax2.set_ylim(ymin, ymax)

    # Add phase markers
    min_date = daily_stats["date"].min()
    max_date = daily_stats["date"].max()

    alpha_end = pd.to_datetime(
        "2025-07-10"
    )  # Presentation at CIRED Recherche en Pratique seminar
    beta_closed_end = pd.to_datetime(
        "2025-09-04"
    )  # Public beta launch with September newsletter

    # Add shaded regions for phases
    ax1.axvspan(
        min_date,
        alpha_end.to_pydatetime(),
        alpha=0.1,
        color="green",
        label="Alpha Phase",
    )

    ax1.axvspan(
        alpha_end.to_pydatetime(),
        beta_closed_end.to_pydatetime(),
        alpha=0.1,
        color="orange",
        label="Beta Closed",
    )
    ax1.axvspan(
        beta_closed_end.to_pydatetime(),
        max_date.to_pydatetime(),
        alpha=0.1,
        color="blue",
        label="Beta Open",
    )

    # Label each shaded phase region
    alpha_mid = min_date + (alpha_end - min_date) / 2
    beta_closed_mid = alpha_end + (beta_closed_end - alpha_end) / 2
    beta_open_mid = beta_closed_end + (max_date - beta_closed_end) / 2

    for x, label, color in [
        (alpha_mid, "Alpha", "green"),
        (beta_closed_mid, "Beta Closed", "orange"),
        (beta_open_mid, "Beta Open", "blue"),
    ]:
        ax1.text(
            x,
            ax1.get_ylim()[0] * 0.9,  # vertical position (tweak 0.97 → higher/lower)
            label,
            color=color,
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=10,
            alpha=0.8,
        )

    # 1) vertical markers (no legend labels to keep legend clean)
    for x, color in [(alpha_end, "green"), (beta_closed_end, "orange")]:
        ax1.axvline(x.to_pydatetime(), linestyle="--", lw=1, color=color, zorder=3)

    # 2) rotated labels anchored near the bottom (works well if you set ylim bottom to -4)
    ymin, ymax = ax1.get_ylim()
    for x, text, color in [
        (alpha_end, "2025-07-10 CIRED presentation", "green"),
        (beta_closed_end, "2025-09-04 Newsletter announcement", "orange"),
    ]:
        ax1.annotate(
            text,
            xy=(x.to_pydatetime(), ymax),  # anchor at top edge
            xytext=(6, -6),  # small offset into the plot
            textcoords="offset points",
            rotation=0,
            va="top",
            ha="left",
            fontsize=10,
            color=color,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8),
            annotation_clip=False,  # show even if slightly outside axes
            zorder=4,
        )

    # Title and legend
    plt.title(
        "Cired.digital activity timeline",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )

    # Combine legends
    lines = line1 + line2
    labels = [str(line.get_label()) for line in lines]

    ax1.legend(lines, labels, loc="upper right", bbox_to_anchor=(0.98, 0.98))

    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha="right")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    plt.show()


plot_session_activity_timeline(
    events_df, save_path="viz1_session_activity_timeline.png"
)
