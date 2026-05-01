# *** imports

# ** infra
from tiferet.events import DomainEvent

# *** events

# ** event: evaluate_expression
class EvaluateExpression(DomainEvent):
    """A simple event that evaluates a single arithmetic expression."""

    # * method: execute
    def execute(self, **kwargs) -> int:
        """Evaluate the expression 1 + 3 - (4 / 2) * 5 + 6 and return the result.

        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The result of the arithmetic expression.
        :rtype: int
        """

        # Evaluate and return the expression.
        return 1 + 3 - (4 / 2) * 5 + 6
