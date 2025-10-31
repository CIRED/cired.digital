"""
Sessions Statistics Script.

This script provides a quick statistical overview of web application session logs
from the CIRED.digital project. It loads session data and generates summary statistics.

The script uses the logloader module to import processed session data as a list of
session dictionaries and performs basic exploratory data analysis to understand:
- Session length distributions
- Event type combinations within sessions
- Common patterns in session event sequences

Usage:
    python describe_sessions.py

Dependencies:
    - logloader: Custom module that provides sessions list

Input:
    Event data is loaded via the logloader module, which processes JSON event files
    from the monitor-logs directory structure.

Output:
    Console output with:
    - Total number of sessions
    - Counts of sessions by event length (1, 2, 3+)
    - Event type combinations for sessions with 1, 2, and 3+ events for exploratory analysis.

Author: Ha Duong Minh
Created: October 2025
"""

from collections import Counter, OrderedDict
from typing import Any

from logloader import sessions

print(f"Sessions loaded: {len(sessions)}")

sessions_1 = [s for s in sessions if len(s["events"]) == 1]
print(f"\nSessions with 1 event: {len(sessions_1)}")

# Verification that one event sessions are always a sessionStart
two_event_pairs = {(s["events"][0]["eventType"]) for s in sessions_1}
print(f"\nEvent type for one-event sessions: {two_event_pairs}")


sessions_2 = [s for s in sessions if len(s["events"]) == 2]
print(f"\nSessions with 2 events: {len(sessions_2)}")

# Verification that two event sessions are always a sessionStart and visibilityChange
two_event_pairs = {
    (s["events"][0]["eventType"], s["events"][1]["eventType"]) for s in sessions_2
}
print(f"\nEvent type pairs for two-event sessions: {two_event_pairs}")


sessions_3p = [s for s in sessions if len(s["events"]) >= 3]
print(f"\nSessions with 3+ events: {len(sessions_3p)}")

# What do three+ event sessions start and end with ?
three_plus_event_pairs = Counter(
    (s["events"][0]["eventType"], s["events"][-1]["eventType"]) for s in sessions_3p
)

print("\nStart–end event type counts for three+ event sessions:")
for pair, count in three_plus_event_pairs.most_common():
    print(f"{pair}: {count}")


# Analyze event type distributions in 3+ event sessions
def event_type_distribution(
    sessions: list[dict[str, Any]],
    event_types: tuple[str, ...] = ("request", "article", "response", "feedback"),
) -> dict[str, OrderedDict[int, int]]:
    """
    Count how many of each specified event type occur in each session.

    Returns a dict mapping event_type (str) to an OrderedDict mapping count (int) to number of sessions (int).
    """
    distributions: dict[str, OrderedDict[int, int]] = {}

    for etype in event_types:
        counter = Counter(
            sum(e["eventType"] == etype for e in s["events"]) for s in sessions
        )
        distributions[etype] = OrderedDict(sorted(counter.items()))

    return distributions


distributions = event_type_distribution(sessions_3p)
print("\nEvent type distributions in 3+ event sessions:")
for event_type, counts in distributions.items():
    print(f"{event_type}: {dict(counts)}")
