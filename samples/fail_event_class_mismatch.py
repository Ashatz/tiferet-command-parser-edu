# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: add_error
class AddErr(DomainEvent):
    """Class name AddErr does not match expected AddError for section add_error."""

    # * method: execute
    def execute(self, **kwargs) -> str:
        """Execute."""

        # Return result.
        return 'done'
