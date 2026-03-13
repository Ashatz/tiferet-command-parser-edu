# *** imports

# ** app
from .settings import DomainEvent
from ..interfaces import ErrorService

# *** events

# ** event: get_error
class GetError(DomainEvent):
    """Retrieve an error — but the attribute has no # * member header."""

    error_service: ErrorService

    # * init
    def __init__(self, error_service: ErrorService):
        """Initialize."""

        # Set dependency.
        self.error_service = error_service

    # * method: execute
    def execute(self, id: str, **kwargs) -> str:
        """Retrieve an error."""

        # Return the error.
        return self.error_service.get(id)
