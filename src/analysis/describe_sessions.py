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


# Distribution of session lengths (number of events -> number of sessions)
# Binning 1, 2, 3, 4, 5, 6-10, 11-20, 21+
def _length_bin(n: int) -> str:
    if n <= 5:
        return str(n)
    if 6 <= n <= 10:
        return "6-10"
    if 11 <= n <= 20:
        return "11-20"
    return "21+"


binned_lengths = Counter(_length_bin(len(s["events"])) for s in sessions)
print("\nSession length distribution (number of events -> number of sessions):")
for label in ["1", "2", "3", "4", "5", "6-10", "11-20", "21+"]:
    count = binned_lengths.get(label, 0)
    if count:
        print(f"{label}: {count}")

# Distribution of session durations
# Calculate session durations as floats (seconds)
session_durations = []
for s in sessions:
    start = s["events"][0]["timestamp"]
    end = s["events"][-1]["timestamp"]
    if start is None or end is None:
        continue
    delta = end - start  # pandas.Timedelta
    try:
        seconds = float(delta.total_seconds())
    except Exception:
        # Fallback: if delta is naive, try using Python's total_seconds
        seconds = (end - start).total_seconds()  # type: ignore[attr-defined]
    session_durations.append(seconds)


# Print session duration statistics (number of seconds -> number of events)
# Binning: 0, 1-5, 6-10, 11-30, 31-60, 61-300, 301-600, 601+
def _duration_bin(seconds: float) -> str:
    if seconds < 1:
        return "0"
    if 1 <= seconds <= 5:
        return "1-5"
    if 6 <= seconds <= 10:
        return "6-10"
    if 11 <= seconds <= 30:
        return "11-30"
    if 31 <= seconds <= 60:
        return "31-60"
    if 61 <= seconds <= 300:
        return "61-300"
    if 301 <= seconds <= 600:
        return "301-600"
    return "601+"


binned_durations = Counter(_duration_bin(d) for d in session_durations)
print("\nSession duration distribution (seconds -> number of sessions):")
for label in ["0", "1-5", "6-10", "11-30", "31-60", "61-300", "301-600", "601+"]:
    count = binned_durations.get(label, 0)
    if count:
        print(f"{label}: {count}")
