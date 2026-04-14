# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: ping
class Ping(DomainEvent):
    """A minimal event with no attributes and a single method."""

    # * method: execute
    def execute(self, **kwargs) -> str:
        """Return a static response."""

        # Return pong.
        return 'pong'
