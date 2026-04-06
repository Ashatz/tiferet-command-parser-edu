"""Tiferet Invalid Annotation Sample — malformed obsolete and todo annotations"""

# *** imports

# ** app
from .settings import DomainEvent, a
from ..interfaces import ErrorService

# *** events

# ** event: get_error
# -- obsolete
class GetError(DomainEvent):
    '''
    An event with a malformed group-level obsolete annotation.
    The annotation is missing a colon and description, so the lexer
    emits LINE_COMMENT instead of OBSOLETE.
    '''

    # * attribute: error_service
    error_service: ErrorService

    # * init
    def __init__(self, error_service: ErrorService):
        '''
        Initialize the GetError event.

        :param error_service: The error service.
        :type error_service: ErrorService
        '''

        # Set the error service dependency.
        self.error_service = error_service

    # * method: execute
    # + todo
    def execute(self, id: str, **kwargs):
        '''
        Retrieve an error by its ID.

        :param id: The error identifier.
        :type id: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        '''

        # Retrieve the error from the service.
        error = self.error_service.get(id)

        # Verify the error exists.
        self.verify(
            expression=error is not None,
            error_code=a.const.ERROR_NOT_FOUND_ID,
            id=id,
        )

        # Return the error.
        return error
