# *** imports

from typing import List
from .settings import DomainEvent

# *** events

# ** event: ping
class Ping(DomainEvent):
    """Minimal event."""

    # * method: execute
    def execute(self, **kwargs) -> str:
        """Execute."""

        # Return pong.
        return 'pong'
