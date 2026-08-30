from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class MLPrediction:
    """A prediction is optional and never replaces evidence-backed findings."""

    label: str
    confidence: float | None = None
    explanation: str | None = None
    metadata: dict[str, Any] | None = None
    model_name: str | None = None
    model_version: str | None = None
    feature_schema_version: str | None = None
    probability: float | None = None
    calibration_metadata: dict[str, Any] | None = None
    explanation_metadata: dict[str, Any] | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


__all__ = ["MLPrediction"]
