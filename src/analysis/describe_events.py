"""
Event Log Statistics Analysis Script.

This script provides a quick statistical overview of web application event logs
from the CIRED.digital project. It loads event data and generates summary statistics
including event type distributions and payload structure analysis.

The script uses the logloader module to import processed event data as a pandas DataFrame
and performs basic exploratory data analysis to understand:
- Event type frequency and distribution
- Data structure and schema validation
- Payload field analysis by event type

Usage:
    python describe_events.py

Dependencies:
    - pandas: For data manipulation and analysis
    - logloader: Custom module that provides events_df DataFrame

Input:
    Event data is loaded via the logloader module, which processes JSON event files
    from the monitor-logs directory structure.

Output:
    Console output with:
    - DataFrame overview (shape, columns, types)
    - Event type frequency table with percentages
    - Payload structure breakdown by event type
    - Sample event data

Author: Ha Duong Minh
Created: October 2025
"""

import pandas as pd
from logloader import events_df

print(events_df.head())
print(events_df["eventType"].value_counts())

print(f"\nDataFrame shape: {events_df.shape}")
print(f"\nColumns: {events_df.columns.tolist()}")
print("\nData types:")
print(events_df.dtypes)
print("\nExample event:")
print(events_df.iloc[[0]].T)


print("\n" + "=" * 60)
print("EVENTS BY TYPE")
print("=" * 60)

# More explicit version that's type-checker friendly
value_counts_series = events_df["eventType"].value_counts()
event_type_df = pd.DataFrame(
    {
        "eventType": value_counts_series.index,
        "count": value_counts_series.values,
    }
)
event_type_df["percentage"] = (
    event_type_df["count"] / event_type_df["count"].sum() * 100
).round(2)
print(event_type_df.to_string(index=False))

print("\n" + "=" * 60)
print("PAYLOAD STRUCTURE BY EVENT TYPE")
print("=" * 60)

# Extract payload keys for each event type
payload_structure = []
for event_type in sorted(events_df["eventType"].unique()):
    type_df = events_df[events_df["eventType"] == event_type]
    all_keys: set[str] = set()
    for payload in type_df["payload"]:
        if isinstance(payload, dict):
            all_keys.update(payload.keys())

    payload_structure.append(
        {
            "eventType": event_type,
            "count": len(type_df),
            "payload_keys": sorted(list(all_keys)),
        }
    )

payload_df = pd.DataFrame(payload_structure)
for _, row in payload_df.iterrows():
    print(f"\n{row['eventType']} ({row['count']} events):")
    print(f"  Keys: {', '.join(row['payload_keys'])}")
