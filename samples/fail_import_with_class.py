# *** imports

# ** app
from .settings import DomainEvent

# ** core
class BadHelper(DomainEvent):
    """This class should not be inside an import section."""

    # * method: execute
    def execute(self, **kwargs) -> str:
        """Bad."""

        # Return bad.
        return 'bad'

# *** events

# ** event: ping
class Ping(DomainEvent):
    """A valid event."""

    # * method: execute
    def execute(self, **kwargs) -> str:
        """Return pong."""

        # Return pong.
        return 'pong'
