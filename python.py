from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET

import pandas as pd
from Evtx.Evtx import Evtx


INPUT_FILE = Path("system_logs.evtx")
CSV_OUTPUT = Path("logs_dataset.csv")
SUMMARY_OUTPUT = Path("analysis_summary.txt")


NAMESPACE = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}


def get_text(node, path, attribute=None):
    """Safely read text or an attribute from an XML node."""
    result = node.find(path, NAMESPACE)
    if result is None:
        return None
    if attribute:
        return result.attrib.get(attribute)
    return result.text


def parse_event(xml_text):
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return {
            "event_id": None,
            "level": None,
            "provider": None,
            "timestamp": None,
            "computer": None,
            "message": xml_text[:500],
            "raw_xml": xml_text,
        }
        
        
    system = root.find("e:System", NAMESPACE)
    event_data = root.find("e:EventData", NAMESPACE)

    message_parts = []
    if event_data is not None:
        for data in event_data.findall("e:Data", NAMESPACE):
            if data.text:
                message_parts.append(data.text.strip())

    return {
        "event_id": get_text(system, "e:EventID") if system is not None else None,
        "level": get_text(system, "e:Level") if system is not None else None,
        "provider": get_text(system, "e:Provider", attribute="Name") if system is not None else None,
        "timestamp": get_text(system, "e:TimeCreated", attribute="SystemTime") if system is not None else None,
        "computer": get_text(system, "e:Computer") if system is not None else None,
        "message": " | ".join(message_parts) if message_parts else None,
        "raw_xml": xml_text,
    }


def build_summary(df):
    """Create a lightweight text report for quick inspection."""
    provider_counts = Counter(df["provider"].dropna())
    level_counts = Counter(df["level"].dropna())
    event_counts = Counter(df["event_id"].dropna())

    lines = [
        "AI Log Analyzer Summary",
        "=" * 24,
        f"Total records: {len(df)}",
        f"Unique providers: {df['provider'].nunique(dropna=True)}",
        f"Unique event IDs: {df['event_id'].nunique(dropna=True)}",
        "",
        "Top 5 providers:",
    ]

    for provider, count in provider_counts.most_common(5):
        lines.append(f"- {provider}: {count}")

    lines.append("")
    lines.append("Top 5 levels:")
    for level, count in level_counts.most_common(5):
        lines.append(f"- Level {level}: {count}")

    lines.append("")
    lines.append("Top 5 event IDs:")
    for event_id, count in event_counts.most_common(5):
        lines.append(f"- Event ID {event_id}: {count}")

    return "\n".join(lines)


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input log file not found: {INPUT_FILE}")

    logs = []
    with Evtx(str(INPUT_FILE)) as log:
        for record in log.records():
            logs.append(parse_event(record.xml()))

    df = pd.DataFrame(logs)
    df.to_csv(CSV_OUTPUT, index=False)

    summary = build_summary(df)
    SUMMARY_OUTPUT.write_text(summary, encoding="utf-8")

    print(f"Structured logs saved to {CSV_OUTPUT}")
    print(f"Summary report saved to {SUMMARY_OUTPUT}")


if __name__ == "__main__":
    main()
    
