"""Semantic failure: event references ErrorService which is never imported."""

# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: save_error
class SaveError(DomainEvent):
    """An event that injects ErrorService without importing it."""

    # * attribute: error_service
    error_service: ErrorService

    # * init
    def __init__(self, error_service: ErrorService):
        """Initialize with the error service."""

        # Set the error service dependency.
        self.error_service = error_service

    # * method: execute
    def execute(self, id: str, name: str, **kwargs) -> str:
        """Save an error using the unresolved service type."""

        # Save the error.
        self.error_service.save(id, name)
