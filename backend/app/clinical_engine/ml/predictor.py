from typing import Any, Protocol

from app.clinical_engine.ml.schemas import MLPrediction


class Predictor(Protocol):
    def predict(self, context: Any, proposed_medications: Any) -> MLPrediction | None: ...

    def predict_adverse_reaction(
        self, context: Any, proposed_medications: Any
    ) -> MLPrediction | None: ...

    def predict_dose(self, context: Any, proposed_medications: Any) -> MLPrediction | None: ...

    def predict_response(self, context: Any, proposed_medications: Any) -> MLPrediction | None: ...


class NullPredictor:
    """Default predictor: no model is available, so no unsupported output is emitted."""

    def predict(self, context: Any, proposed_medications: Any) -> None:
        del context, proposed_medications
        return None

    def predict_adverse_reaction(self, context: Any, proposed_medications: Any) -> None:
        return self.predict(context, proposed_medications)

    def predict_dose(self, context: Any, proposed_medications: Any) -> None:
        return self.predict(context, proposed_medications)

    def predict_response(self, context: Any, proposed_medications: Any) -> None:
        return self.predict(context, proposed_medications)


__all__ = ["NullPredictor", "Predictor"]
