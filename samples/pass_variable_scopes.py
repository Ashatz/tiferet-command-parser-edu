"""A calculator event that demonstrates local variables across data types and method scopes, plus arithmetic assignments that validate inferred types."""

# *** imports

# ** infra
from tiferet.events import DomainEvent

# *** events

# ** event: scoped_calc
class ScopedCalc(DomainEvent):
    """An event with class state and locals across multiple method scopes."""

    # * attribute: base
    base: int

    # * method: prepare
    def prepare(self, factor: int) -> int:
        """Return a method-local int derived from a class attribute and an int parameter.

        :param factor: A scaling factor.
        :type factor: int
        :return: The prepared value.
        :rtype: int
        """

        # A method-local int variable.
        scaled = self.base * factor

        # Return the computed value.
        return scaled

    # * method: execute
    def execute(self, a: int, b: int) -> int:
        """Combine multiple typed locals (int, float, str) and return an int.

        :param a: The first operand.
        :type a: int
        :param b: The second operand.
        :type b: int
        :return: The combined arithmetic result.
        :rtype: int
        """

        # Method-local int with a literal RHS.
        offset = 7

        # Method-local float to demonstrate a different inferred type.
        ratio = 1.5

        # Method-local str distinct from numeric variables.
        label = 'total'

        # Arithmetic assignment that the type checker validates against the int operands.
        total = a + b + offset

        # Return total so the resolver references local, parameter, and self scopes.
        return total
