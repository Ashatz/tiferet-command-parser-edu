"""Semantic failure: assigns a str-typed local to an int-typed class attribute, demonstrating an assignment type mismatch between two variables of different declared types."""

# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: assign_var
class AssignVar(DomainEvent):
    """An event that assigns a str local to an int-typed class attribute."""

    # * attribute: count
    count: int

    # * method: execute
    def execute(self, a: int) -> int:
        """Define a str local and assign it to the int-typed `self.count`.

        :param a: An int parameter that the type checker can also reference.
        :type a: int
        :return: A placeholder int value (the violation is the assignment above).
        :rtype: int
        """

        # Method-local str variable.
        label = 'not_a_number'

        # Assigning a str to an int-typed attribute — type checker flags this.
        self.count = label

        # Return a literal so the rest of the body type-checks cleanly.
        return a
