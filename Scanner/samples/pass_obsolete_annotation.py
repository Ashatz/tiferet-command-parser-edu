"""Tiferet RenameError Event Sample — Obsolete Annotations"""

# *** imports

# ** app
from .settings import DomainEvent, a
from ..interfaces import ErrorService

# *** events

# ** event: rename_error
# -- obsolete: superseded by ErrorAggregate.rename(); use UpdateError instead
class RenameError(DomainEvent):
    """
    Command to rename an existing Error domain object.
    """

    # * attribute: error_service
    error_service: ErrorService

    # * init
    def __init__(self, error_service: ErrorService):
        """
        Initialize the RenameError command.

        :param error_service: The error service to use.
        :type error_service: ErrorService
        """
        self.error_service = error_service

    # * method: execute
    # - obsolete: inline rename logic; delegate to error_service.rename() instead
    def execute(self, id: str, name: str, **kwargs) -> str:
        """
        Rename an existing Error by its ID.

        :param id: The unique identifier of the error.
        :type id: str
        :param name: The new name for the error.
        :type name: str
        :param kwargs: Additional context.
        :type kwargs: dict
        :return: The unique identifier of the updated error.
        :rtype: str
        """

        # Retrieve the existing error.
        error = self.error_service.get(id)
        self.verify(
            expression=error is not None,
            error_code=a.const.ERROR_NOT_FOUND_ID,
            message=f'Error not found: {id}.',
            id=id
        )

        # Rename the error.
        error.set_attribute('name', name)

        # Save the updated error.
        self.error_service.save(error)

        # Return the updated error id.
        return id
