"""Tiferet RemoveErrorMessage event sample."""

# *** imports

# ** app
from .settings import DomainEvent, a
from ..domain import Error
from ..interfaces import ErrorService

# *** events

# ** event: remove_error_message
class RemoveErrorMessage(DomainEvent):
    """
    Command to remove a message from an existing Error domain object.
    """

    # * attribute: error_service
    error_service: ErrorService

    # * init
    def __init__(self, error_service: ErrorService):
        """
        Initialize the RemoveErrorMessage command.

        :param error_service: The error service to use.
        :type error_service: ErrorService
        """
        self.error_service = error_service

    # * method: execute
    def execute(self, id: str, lang: str = 'en_US', **kwargs) -> str:
        """
        Remove a message from an existing Error by its ID.

        :param id: The unique identifier of the error.
        :type id: str
        :param lang: The language of the message to remove (default is 'en_US').
        :type lang: str
        :param kwargs: Additional context (passed to error if raised).
        :type kwargs: dict
        :return: The unique identifier of the updated error.
        :rtype: str
        """

        # Retrieve the existing error.
        error = self.error_service.get(id)
        self.verify(
            expression=error,
            error_code=a.const.ERROR_NOT_FOUND_ID,
            message=f'Error not found: {id}.',
            id=id
        )

        # Remove the message.
        error.remove_message(lang)

        # Verify that at least one message remains.
        self.verify(
            expression=len(error.message) > 0,
            error_code=a.const.NO_ERROR_MESSAGES_ID,
            message=f'No error messages are defined for error ID {id}.',
            id=id
        )

        # Save the updated error.
        self.error_service.save(error)

        # Return the updated error id.
        return id