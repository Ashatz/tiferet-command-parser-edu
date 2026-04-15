"""Parse failure: class defined without an enclosing # *** group header."""

# *** imports

# ** app
from .settings import DomainEvent

# The events group header is missing entirely.
# The parser expects every section to appear under a # *** group.

# ** event: orphan_event
class OrphanEvent(DomainEvent):
    """An event whose section has no parent group — the parser cannot attach it."""

    # * method: execute
    def execute(self, **kwargs) -> str:
        """Return a greeting."""

        # Return hello.
        return 'hello'
