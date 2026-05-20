"""Hermes-backed LLM consolidator for Ingrain.

Replaces (or augments) the deterministic regex compiler in
src/aeonik_ingrain/compiler/rules.py. Instead of pattern matching, this
consolidator hands recent events to Hermes — running whatever model the user
has Hermes configured against — and parses Hermes's JSON output into cards.

No external API keys. Whatever Hermes uses for its main session is what
consolidates. Cost lives in the user's existing Hermes subscription/quota.

Public API:
    from aeonik_ingrain.integrations.hermes_consolidator import consolidate
    new_cards = consolidate(store, limit=50)
"""

from __future__ import annotations

from aeonik_ingrain.integrations.hermes_consolidator.consolidator import (
    ConsolidationResult,
    consolidate,
    parse_cards,
)

__all__ = ["ConsolidationResult", "consolidate", "parse_cards"]
