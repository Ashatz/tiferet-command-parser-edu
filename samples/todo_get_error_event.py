"""Tiferet GetError Event Sample — TODO Annotations"""

# *** imports

# ** app
from .settings import DomainEvent, a
from ..domain import Error
from ..interfaces import ErrorService

# *** events

# ** event: get_error
# ++ todo: add CacheService injection to cache retrieved errors
class GetError(DomainEvent):
    """
    Command to retrieve an existing Error domain object by its ID.
    """

    # * attribute: error_service
    error_service: ErrorService

    # * init
    def __init__(self, error_service: ErrorService):
        """
        Initialize the GetError command.

        :param error_service: The error service to use.
        :type error_service: ErrorService
        """
        self.error_service = error_service

    # * method: execute
    # + todo: validate lang parameter against supported locales before retrieval
    def execute(self, id: str, **kwargs) -> Error:
        """
        Retrieve an Error by its ID.

        :param id: The unique identifier of the error.
        :type id: str
        :param kwargs: Additional context.
        :type kwargs: dict
        :return: The retrieved Error domain object.
        :rtype: Error
        """

        # Retrieve the error from the service.
        error = self.error_service.get(id)

        # Verify the error exists.
        self.verify(
            expression=error is not None,
            error_code=a.const.ERROR_NOT_FOUND_ID,
            message=f'Error not found: {id}.',
            id=id
        )

        # Return the retrieved error.
        return error
