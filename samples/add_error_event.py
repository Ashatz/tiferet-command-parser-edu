"""Tiferet Add Error Event Sample"""

# *** imports

# ** core
from typing import (
    List,
    Dict,
    Any
)

# ** app
from .settings import DomainEvent, a
from ..domain import Error
from ..interfaces import ErrorService
from ..mappers import Aggregate, ErrorAggregate

# *** events

# ** event: add_error
class AddError(DomainEvent):
    """
    Command to add a new Error domain object to the repository.
    """

    # * attribute: error_service
    error_service: ErrorService

    # * init
    def __init__(self, error_service: ErrorService):
        """
        Initialize the AddError command.

        :param error_repo: The error service to use.
        :type error_repo: ErrorService
        """
        self.error_service = error_service

    # * method: execute
    @DomainEvent.parameters_required(['id', 'name', 'message'])
    def execute(self,id: str, name: str, message: str, lang: str = 'en_US', additional_messages: List[Dict[str, Any]] = []) -> None:
        """
        Add a new Error to the app.

        :param id: The unique identifier of the error.
        :type id: str
        :param name: The name of the error.
        :type name: str
        :param message: The primary error message text.
        :type message: str
        :param lang: The language of the primary error message (default is 'en_US').
        :type lang: str
        :param additional_messages: Additional error messages in different languages.
        :type additional_messages: List[Dict[str, Any]]
        """

        # Check if an error with the same ID already exists.
        exists = self.error_service.exists(id)
        self.verify(
            expression=exists is False,
            error_code=a.const.ERROR_ALREADY_EXISTS_ID,
            message=f'An error with ID {id} already exists.',
            id=id
        )

        # Create the Error aggregate.
        error_messages = [{'lang': lang, 'text': message}] + additional_messages
        new_error = Aggregate.new(
            ErrorAggregate,
            id=id,
            name=name,
            message=error_messages
        )

        # Save the new error.
        self.error_service.save(new_error)

        # Return the new error.
        return new_error