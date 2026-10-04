class NotFoundError(ValueError):
    """Raised when the requested entity does not exist (the API maps it to 404)."""
