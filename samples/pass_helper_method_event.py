"""A calculator event with a helper method to convert values to integers."""

# *** imports

# ** infra
from tiferet.events import DomainEvent

# *** events

# ** event: add_integer
class AddInteger(DomainEvent):
    """An event that adds two numbers and returns an integer result."""

    # * method: to_int
    def to_int(self, value: str) -> int:
        """Convert a value to an integer.

        :param value: The value to convert.
        :type value: str
        :return: The integer representation.
        :rtype: int
        """

        # Return the integer conversion.
        return int(value)

    # * method: execute
    def execute(self, a: str, b: str, **kwargs) -> int:
        """Add two values as integers.

        :param a: The first operand.
        :type a: str
        :param b: The second operand.
        :type b: str
        :return: The integer sum.
        :rtype: int
        """

        # Convert inputs to integers.
        x = self.to_int(a)
        y = self.to_int(b)

        # Return the sum.
        return x + y
