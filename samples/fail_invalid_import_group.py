# *** imports

# ** infra_utils
from typing import Any

# *** events

# ** event: ping
class Ping(DomainEvent):
    """A minimal event with an invalid import group above."""

    # * method: execute
    def execute(self, **kwargs) -> str:
        """Return pong."""

        # Return pong.
        return 'pong'
