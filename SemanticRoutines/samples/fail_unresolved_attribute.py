"""Semantic failure: method body references self.logger, which is never declared as a class attribute."""

# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: log_result
class LogResult(DomainEvent):
    """An event that references an attribute not declared on the class."""

    # * attribute: message
    message: str

    # * init
    def __init__(self, message: str):
        """Initialize with a message."""

        # Set the message attribute.
        self.message = message

    # * method: execute
    def execute(self, **kwargs) -> str:
        """Attempt to log using an undeclared attribute."""

        # Reference an attribute that was never declared in the class scope.
        self.logger.info(self.message)

        # Return the message.
        return self.message
