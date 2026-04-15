"""Semantic failure: assigns a str literal to an int-typed attribute and adds int + str."""

# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: bad_math
class BadMath(DomainEvent):
    """An event with type mismatches in assignment and operation."""

    # * attribute: count
    count: int

    # * init
    def __init__(self, count: int):
        """Initialize with a count."""

        # Assign a string literal to an int-typed attribute.
        self.count = 'not_a_number'

    # * method: execute
    def execute(self, a: int, b: int) -> int:
        """Attempt arithmetic with incompatible types."""

        # Add an int parameter to a str literal.
        return a + 'hello'
