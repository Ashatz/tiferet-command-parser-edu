# *** imports

# ** app
from .settings import DomainEvent, a
from ..interfaces import ErrorService

# *** events

# -- obsolete: replaced by UpdateError in v2.0
# ** event: rename_error
class RenameError(DomainEvent):
    """Rename an existing error object."""

    # * attribute: error_service
    error_service: ErrorService

    # * init
    def __init__(self, error_service: ErrorService):
        """Initialize with error service."""

        # Set the error service dependency.
        self.error_service = error_service

    # + todo: add parameter validation decorator
    # * method: execute
    def execute(self, id: str, name: str, **kwargs) -> str:
        """Rename an error by ID."""

        # Retrieve the error.
        error = self.error_service.get(id)

        # Verify existence.
        self.verify(
            expression=error is not None,
            error_code=a.const.ERROR_NOT_FOUND_ID,
            id=id,
        )

        # Rename and save.
        error.set_attribute('name', name)
        self.error_service.save(error)

        # Return the ID.
        return id
