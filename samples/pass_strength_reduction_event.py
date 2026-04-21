"""An event that demonstrates strength reduction: arithmetic on power-of-two
literals (and exponentiation by 2) is rewritten into cheaper shifts or
self-multiplication at compile time."""

# *** imports

# ** infra
from tiferet.events import DomainEvent

# *** events

# ** event: compute_metrics
class ComputeMetrics(DomainEvent):
    """Compute a trio of values exercising each strength-reduction pattern."""

    # * method: execute
    def execute(self, value: int, **kwargs) -> int:
        """Compute the combined metric.

        :param value: The raw input value.
        :type value: int
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The combined metric (sum of the three reduced values).
        :rtype: int
        """

        # Multiplication by a power of two: `value * 8` reduces to `value << 3`.
        scaled = value * 8

        # Division by a power of two: `value / 4` reduces to `value >> 2`.
        halved = value / 4

        # Exponentiation by two: `value ** 2` reduces to `value * value`.
        squared = value ** 2

        # Return the combined metric.
        return scaled + halved + squared
