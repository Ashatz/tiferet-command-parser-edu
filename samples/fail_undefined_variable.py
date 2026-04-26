"""Semantic failure: the execute method references `missing`, which is never declared as a parameter, attribute, or local variable."""

# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: undefined_use
class UndefinedUse(DomainEvent):
    """An event that references a name that does not exist in any scope."""

    # * method: execute
    def execute(self, a: int) -> int:
        """Reference an undefined variable in the return expression.

        :param a: A value passed in by the caller.
        :type a: int
        :return: An int formed by adding `a` to the undefined `missing` symbol.
        :rtype: int
        """

        # `missing` is not declared anywhere — the name resolver should flag it.
        return a + missing
