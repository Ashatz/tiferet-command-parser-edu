# *** imports

# ** app
from .settings import DomainEvent

# *** events

class Ping(DomainEvent):
    """Ping event — but the class has no # ** section header above it."""

    # * method: execute
    def execute(self, **kwargs) -> str:
        """Execute."""

        # Return pong.
        return 'pong'
