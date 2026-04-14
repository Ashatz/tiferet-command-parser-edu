"""Sample event for testing minimal injection and execution of a domain event."""

# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: ping
class Ping(DomainEvent):

    # * attribute: pong
    pong: str

    # * init
    def __init__(self, pong: str):
        """Initialize with a pong string."""

        # Set the pong attribute.
        self.pong = pong

    # * method: execute
    def execute(self, **kwargs) -> str:
        """Return the injected pong string."""

        # Return the pong string.
        return self.pong
