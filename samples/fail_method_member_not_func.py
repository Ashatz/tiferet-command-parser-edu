# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: ping
class Ping(DomainEvent):
    """Event where a method member wraps a variable instead of a function."""

    # * method: execute
    execute: str
