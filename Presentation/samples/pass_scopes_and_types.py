# *** imports

# ** infra
from tiferet.events import DomainEvent

# *** events

# ** event: score_calculator
class ScoreCalculator(DomainEvent):
    """An event that computes a weighted score from class and method-local variables."""

    # * attribute: base_points
    base_points: int

    # * attribute: multiplier
    multiplier: float

    # * method: apply_bonus
    def apply_bonus(self, points: int) -> int:
        """Add a fixed bonus to a point value.

        :param points: The input points to adjust.
        :type points: int
        :return: The adjusted point value with bonus applied.
        :rtype: int
        """

        # Method-local int declared in this scope (separate from class scope).
        bonus = '10'

        # Return points combined with the local bonus (cross-scope: param + local).
        return points + bonus

    # * method: execute
    def execute(self, amount: int, **kwargs) -> float:
        """Compute a weighted score using class attributes and method-local variables.

        :param amount: The raw input amount.
        :type amount: int
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The final weighted score.
        :rtype: float
        """

        # Method-local int derived from class attribute and parameter (cross-scope expression).
        adjusted = self.base_points + amount

        # Apply a bonus via a helper method call (function call statement).
        bonus_points = self.apply_bonus(amount)

        # Method-local float derived from class attribute and local int (cross-scope expression).
        weighted = self.multiplier * adjusted + bonus_points

        # Return the final weighted score.
        return weighted
