"""Tiferet Invalid Member Names Sample — digit-prefixed attribute and method"""

# *** imports

# ** core
from typing import Any

# ** app
from .settings import DomainEvent, a
from ..interfaces import ErrorService

# *** events

# ** event: bad_members
class BadMembers(DomainEvent):
    '''
    An event with intentionally malformed attribute and method names.
    The lexer should emit UNKNOWN tokens for digit-prefixed members.
    '''

    # * attribute: 456error_service
    456error_service: ErrorService

    # * init
    def __init__(self, error_service: ErrorService):
        '''
        Initialize the event.

        :param error_service: The error service.
        :type error_service: ErrorService
        '''

        # Set the attribute with a digit-prefixed name.
        self.456error_service = error_service

    # * method: 789execute
    def 789execute(self, id: str, **kwargs) -> None:
        '''
        A method with a digit-prefixed name.

        :param id: The identifier.
        :type id: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        '''

        # Attempt to use the malformed attribute.
        self.456error_service.exists(id)
