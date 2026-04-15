"""This module demonstrates how to define multiple operator events in the Tiferet Dialect, and how to parse them using the event parser"""

# *** imports

# ** infra
from tiferet.events import DomainEvent

# *** events

# ** event: add
class Add(DomainEvent):
    """An event that performs addition of two numbers."""

    # * method: execute
    def execute(self, a: int, b: int) -> int:
        """Return the sum of a and b."""

        return a + b

# ** event: subtract
class Subtract(DomainEvent):
    """An event that performs subtraction of two numbers."""

    # * method: execute
    def execute(self, a: int, b: int) -> int:
        """Return the difference of a and b."""

        return a - b

# ** event: multiply
class Multiply(DomainEvent):
    """An event that performs multiplication of two numbers."""

    # * method: execute
    def execute(self, a: int, b: int) -> int:
        """Return the product of a and b."""

        return a * b

# ** event: divide
class Divide(DomainEvent):
    """An event that performs division of two numbers."""

    # * method: execute
    def execute(self, a: int, b: int) -> float:
        """Return the quotient of a and b."""

        return a / b

# ** event: modulus
class Modulus(DomainEvent):
    """An event that performs modulus of two numbers."""

    # * method: execute
    def execute(self, a: int, b: int) -> int:
        """Return the modulus of a and b."""

        return a % b

# ** event: exponentiate
class Exponentiate(DomainEvent):
    """An event that performs exponentiation of two numbers."""

    # * method: execute
    def execute(self, a: int, b: int) -> float:
        """Return a raised to the power of b."""

        return a ** b
