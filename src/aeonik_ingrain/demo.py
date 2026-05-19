"""Runnable launch demos for Aeonik Ingrain."""

from __future__ import annotations

import tempfile
from pathlib import Path

from aeonik_ingrain.compiler.hydrate import hydrate
from aeonik_ingrain.compiler.pages import compile_store
from aeonik_ingrain.db import IngrainStore


DEMO_EVENTS = {
    "correction": [
        ("assistant", "I will describe Aeonik Ingrain as a generic memory layer."),
        (
            "user",
            "No, that's wrong. Don't call this a memory layer; call it a learned "
            "experience layer for autonomous agents.",
        ),
    ],
    "banana": [
        (
            "user",
            "Remember: For this project, yellow CTA buttons are called bananas. "
            "Never ship bananas in enterprise demos.",
        ),
    ],
    "stale-plan": [
        ("user", "Decision: The product name is MindCompiler."),
        ("user", "Decision: Product name is Aeonik Ingrain, not MindCompiler."),
    ],
}

DEMO_QUERIES = {
    "correction": "write the public launch framing",
    "banana": "review this enterprise landing page CTA plan",
    "stale-plan": "what is the product name?",
}


def run_demo(name: str, *, home: str | Path | None = None) -> str:
    """Run a deterministic demo and return a terminal-style transcript."""
    if name not in DEMO_EVENTS:
        raise ValueError(f"Unknown demo {name!r}. Choose one of: {', '.join(sorted(DEMO_EVENTS))}")

    if home:
        return _run_demo_in_store(name, IngrainStore(home))

    with tempfile.TemporaryDirectory(prefix=f"ingrain-demo-{name}-") as tmp:
        return _run_demo_in_store(name, IngrainStore(Path(tmp) / ".ingrain"))


def _run_demo_in_store(name: str, store: IngrainStore) -> str:
    store.initialize()
    lines = [
        f"Aeonik Ingrain Demo: {name}",
        "",
        "Session A: teach the agent",
    ]
    for idx, (actor, text) in enumerate(DEMO_EVENTS[name]):
        store.add_event(
            source="demo",
            runner="hermes",
            event_type="interaction",
            actor=actor,
            text=text,
            created_at=f"2026-05-19T00:00:{idx:02d}+00:00",
        )
        lines.append(f"{actor}> {text}")

    result = compile_store(store)
    query = DEMO_QUERIES[name]
    context = hydrate(store, query=query, limit=8)

    lines.extend(
        [
            "",
            f"Compiled {result['promotions']} learned items.",
            "",
            "Session B: fresh run hydration",
            f"user> {query}",
            "",
            context or "No learned experience found.",
        ]
    )
    return "\n".join(lines)
