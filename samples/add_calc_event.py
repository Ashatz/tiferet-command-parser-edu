"""Tiferet Calculator AddNumber Sample"""

# *** imports

# ** core
from typing import Any

# ** app
from .settings import BasicCalcEvent

# *** events

# ** event: add_number
class AddNumber(BasicCalcEvent):
    '''
    A domain event to perform addition of two numbers.
    '''
    def execute(self, a: Any, b: Any, **kwargs) -> int | float:
        '''
        Execute the addition event.

        :param a: A number representing the first operand.
        :type a: Any
        :param b: A number representing the second operand.
        :type b: Any
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The sum of a and b.
        :rtype: int | float
        '''
        # Verify numeric inputs
        a_verified = self.verify_number(str(a))
        b_verified = self.verify_number(str(b))

        # Add verified values of a and b.
        result = a_verified + b_verified

        # Return the result.
        return result