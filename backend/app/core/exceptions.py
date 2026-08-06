"""Domain exceptions shared by API routes and services."""


class RAPIDLearnError(Exception):
    """Base exception for an expected RAPID-Learn domain error."""


class NotFoundError(RAPIDLearnError):
    """Raised when a requested entity is absent."""
