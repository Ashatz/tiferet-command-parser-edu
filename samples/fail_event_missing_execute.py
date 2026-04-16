# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: ping
class Ping(DomainEvent):
    """Event class with only an attribute and no execute method."""

    # * attribute: pong
    pong: str

    # * init
    def __init__(self, pong: str):
        """Initialize."""

        # Set the pong attribute.
        self.pong = pong
