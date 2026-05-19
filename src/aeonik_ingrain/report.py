"""Human-readable reports."""

from __future__ import annotations

from collections import Counter

from aeonik_ingrain.db import IngrainStore


def build_report(store: IngrainStore) -> str:
    store.initialize()
    events = store.list_events()
    promotions = store.list_promotions()
    current = [p for p in promotions if p.get("current_state") == "current"]
    counts = Counter(p["promoted_type"] for p in current)
    lines = [
        "Aeonik Ingrain Report",
        "",
        f"Home: {store.home}",
        f"Ledger events: {len(events)}",
        f"Current learned items: {len(current)}",
        "",
        "Current counts:",
    ]
    if counts:
        for key in sorted(counts):
            lines.append(f"- {key}: {counts[key]}")
    else:
        lines.append("- none")
    recent = current[-8:]
    if recent:
        lines.extend(["", "Recent learned experience:"])
        for item in recent:
            lines.append(f"- [{item['promoted_type']}] {item['text']} source={item['event_id']}")
    return "\n".join(lines)
