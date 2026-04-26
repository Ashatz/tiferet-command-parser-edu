"""A calculator event that demonstrates parenthesized arithmetic expressions, including the canonical large arithmetic tree 5 * 8 - 6 + (11 - 9 * 7) + 3."""

# *** imports

# ** infra
from tiferet.events import DomainEvent

# *** events

# ** event: paren_calc
class ParenCalc(DomainEvent):
    """An event that exercises parenthesized arithmetic and operator precedence."""

    # * method: execute
    def execute(self, a: int, b: int) -> int:
        """Return a result computed from a, b, and several parenthesized sub-expressions.

        :param a: The first operand.
        :type a: int
        :param b: The second operand.
        :type b: int
        :return: The combined arithmetic result.
        :rtype: int
        """

        # Compute a grouped sub-expression that depends on both parameters.
        grouped = (a + b) * 2

        # The canonical large arithmetic tree: 5*8 - 6 + (11 - 9*7) + 3.
        sample = 5 * 8 - 6 + (11 - 9 * 7) + 3

        # Return the combined result so the parser sees the parens flowing through addition.
        return grouped + sample
