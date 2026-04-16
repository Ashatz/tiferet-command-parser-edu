# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: ping
class Ping(DomainEvent):
    """Event where an attribute member wraps a function instead of a variable."""

    # * attribute: helper
    def helper(self) -> str:
        """This should be a variable, not a function."""

        # Return help.
        return 'help'

    # * method: execute
    def execute(self, **kwargs) -> str:
        """Return pong."""

        # Return pong.
        return 'pong'
