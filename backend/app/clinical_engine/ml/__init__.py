"""Optional machine-learning extension points for the clinical engine."""

from app.clinical_engine.ml.predictor import NullPredictor
from app.clinical_engine.ml.schemas import MLPrediction

__all__ = ["MLPrediction", "NullPredictor"]
