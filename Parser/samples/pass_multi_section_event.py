# *** imports

# ** core
from typing import List

# ** app
from .settings import DomainEvent, a
from ..domain import Error
from ..interfaces import ErrorService

# *** events

# ** event: get_error
class GetError(DomainEvent):
    """Retrieve an error by ID."""

    # * attribute: error_service
    error_service: ErrorService

    # * init
    def __init__(self, error_service: ErrorService):
        """Initialize with error service."""

        # Set the error service dependency.
        self.error_service = error_service

    # * method: execute
    def execute(self, id: str, **kwargs) -> Error:
        """Retrieve an error."""

        # Retrieve the error.
        error = self.error_service.get(id)

        # Verify existence.
        self.verify(
            expression=error is not None,
            error_code=a.const.ERROR_NOT_FOUND_ID,
            id=id,
        )

        # Return the error.
        return error

# ** event: list_errors
class ListErrors(DomainEvent):
    """List all errors."""

    # * attribute: error_service
    error_service: ErrorService

    # * init
    def __init__(self, error_service: ErrorService):
        """Initialize with error service."""

        # Set the error service dependency.
        self.error_service = error_service

    # * method: execute
    def execute(self, **kwargs) -> List:
        """Return all errors."""

        # Retrieve all errors.
        errors = self.error_service.list()

        # Return the list.
        return errors
