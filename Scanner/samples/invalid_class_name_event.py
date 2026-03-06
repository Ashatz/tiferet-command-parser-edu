"""Tiferet Invalid Class Name Sample — digit-prefixed event identifier"""

# *** imports

# ** core
from typing import Any

# ** app
from .settings import DomainEvent, a
from ..interfaces import ErrorService

# *** events

# ** event: 123add_error
class 123AddError(DomainEvent):
    '''
    An intentionally malformed event class with a digit-prefixed name.
    The lexer should emit CLASS UNKNOWN LPAREN for this declaration.
    '''

    # * attribute: error_service
    error_service: ErrorService

    # * init
    def __init__(self, error_service: ErrorService):
        '''
        Initialize the event.

        :param error_service: The error service.
        :type error_service: ErrorService
        '''

        # Set the error service dependency.
        self.error_service = error_service

    # * method: execute
    @DomainEvent.parameters_required(['id', 'name'])
    def execute(self, id: str, name: str, **kwargs) -> None:
        '''
        Attempt to add an error.

        :param id: The error identifier.
        :type id: str
        :param name: The error name.
        :type name: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        '''

        # Verify the error does not already exist.
        self.verify(
            expression=not self.error_service.exists(id),
            error_code=a.const.ERROR_ALREADY_EXISTS_ID,
            id=id,
        )

        # Save the error.
        self.error_service.save(id=id, name=name)
