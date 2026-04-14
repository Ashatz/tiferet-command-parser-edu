"""Parse failure: method defined without # * member artifact comment."""

# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: bare_method
class BareMethod(DomainEvent):
    """An event whose method lacks the required # * method: artifact comment."""

    # * attribute: name
    name: str

    # * init
    def __init__(self, name: str):
        """Initialize with a name."""

        # Set the name attribute.
        self.name = name

    # The # * method: execute artifact comment is missing here.
    # The parser expects every method to be preceded by its member artifact.
    def execute(self, **kwargs) -> str:
        """Return the name."""

        # Return the name.
        return self.name
