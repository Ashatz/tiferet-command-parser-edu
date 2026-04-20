"""An event that demonstrates constant folding: arithmetic sub-expressions
composed entirely of numeric literals can be evaluated at compile time."""

# *** imports

# ** infra
from tiferet.events import DomainEvent

# *** events

# ** event: compute_adjusted_score
class ComputeAdjustedScore(DomainEvent):
    """Compute a score with a fixed scaling factor applied to a penalty."""

    # * method: execute
    def execute(self, base_score: int, penalty: int, **kwargs) -> int:
        """Compute the adjusted score.

        :param base_score: The raw score before adjustment.
        :type base_score: int
        :param penalty: The penalty factor to apply.
        :type penalty: int
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The adjusted score after applying a fixed bonus.
        :rtype: int
        """

        # Subtract the scaled penalty: 3 * 5 is a constant sub-expression.
        adjusted = base_score - 3 * 5 * penalty

        # Return the score with a fixed bonus: 4 * 5 is a constant sub-expression.
        return adjusted + 4 * 5
