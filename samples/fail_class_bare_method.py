# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: ping
class Ping(DomainEvent):
    """Ping event — but the method has no # * member header."""

    def execute(self, **kwargs) -> str:
        """Execute."""

        # Return pong.
        return 'pong'
