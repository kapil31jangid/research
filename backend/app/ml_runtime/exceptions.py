"""Failures isolated from the adaptive learning transaction."""


class ResponsePredictionError(RuntimeError):
    """Raised when an optional predictor cannot safely produce a probability."""
