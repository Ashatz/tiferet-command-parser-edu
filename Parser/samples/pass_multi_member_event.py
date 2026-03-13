# *** imports

# ** core
from typing import List

# ** app
from .settings import DomainEvent, a
from ..interfaces import ErrorService

# *** events

# ** event: list_errors
class ListErrors(DomainEvent):
    """Event to list all error objects."""

    # * attribute: error_service
    error_service: ErrorService

    # * init
    def __init__(self, error_service: ErrorService):
        """
        Initialize the ListErrors event.

        :param error_service: The error service dependency.
        :type error_service: ErrorService
        """

        # Set the error service dependency.
        self.error_service = error_service

    # * method: execute
    @DomainEvent.parameters_required(['limit'])
    def execute(self, limit: int = 100, **kwargs) -> List:
        """
        Retrieve all errors up to a limit.

        :param limit: Maximum number of errors to return.
        :type limit: int
        :return: A list of errors.
        :rtype: List
        """

        # Retrieve all errors from the service.
        errors = self.error_service.list()

        # Verify at least one error exists.
        self.verify(
            expression=len(errors) > 0,
            error_code=a.const.NO_ERRORS_FOUND_ID,
        )

        # Return the truncated list.
        return errors[:limit]
