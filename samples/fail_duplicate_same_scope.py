"""Semantic failure: the execute method assigns the local `total` twice in the same scope."""

# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: dup_var
class DupVar(DomainEvent):
    """An event that defines the same local variable twice in a single scope."""

    # * method: execute
    def execute(self, a: int, b: int) -> int:
        """Define `total` twice within the same method scope.

        :param a: The first operand.
        :type a: int
        :param b: The second operand.
        :type b: int
        :return: The final value of `total`.
        :rtype: int
        """

        # First definition — registered as a method-local VARIABLE.
        total = a + b

        # Re-assignment of the same local name in the same scope — flagged.
        total = a - b

        # Return the local so it is also a referenced symbol.
        return total
