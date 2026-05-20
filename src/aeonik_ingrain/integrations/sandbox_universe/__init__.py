"""Ingrain integration with Sandbox Universe.

Exposes IngrainLane and IngrainSidecarLane — LaneAdapter implementations
that the sandbox-universe runner discovers via Python entry points. Used by:

    sandbox-universe run --lane ingrain
    sandbox-universe run --lane ingrain-sidecar
"""

from __future__ import annotations

from aeonik_ingrain.integrations.sandbox_universe.lane import (
    IngrainLane,
    IngrainLLMSidecarLane,
    IngrainSidecarLane,
)

__all__ = ["IngrainLane", "IngrainLLMSidecarLane", "IngrainSidecarLane"]
