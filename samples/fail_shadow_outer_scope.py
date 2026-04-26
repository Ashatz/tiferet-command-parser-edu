"""Semantic failure: the execute method declares a local `count` that shadows the class attribute `count` defined in the enclosing class scope."""

# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: shadow_var
class ShadowVar(DomainEvent):
    """An event whose local variable shadows an attribute defined on the same class."""

    # * attribute: count
    count: int

    # * method: execute
    def execute(self, a: int) -> int:
        """Declare a local `count` that shadows the outer class attribute.

        :param a: An offset added to the shadowed local.
        :type a: int
        :return: The combined int value.
        :rtype: int
        """

        # `count` already exists in the enclosing class scope — flagged as shadowing.
        count = 5

        # Return the shadowed local plus a parameter.
        return count + a
