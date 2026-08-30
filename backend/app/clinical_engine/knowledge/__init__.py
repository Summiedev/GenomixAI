"""Validated, manually curated clinical knowledge datasets."""

from app.clinical_engine.knowledge.loader import (
    CardiovascularKnowledgeBase,
    load_cardiovascular_knowledge,
)

__all__ = ["CardiovascularKnowledgeBase", "load_cardiovascular_knowledge"]
