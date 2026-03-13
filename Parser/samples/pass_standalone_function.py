# *** imports

# ** core
from typing import Any

# *** utils

# ** util: format_result
def format_result(value: Any, precision: int = 2) -> str:
    """
    Format a computation result as a string.

    :param value: The value to format.
    :type value: Any
    :param precision: Decimal places.
    :type precision: int
    :return: Formatted result string.
    :rtype: str
    """

    # Check if the value is a float.
    if isinstance(value, float):
        return f'{value:.{precision}f}'

    # Otherwise return as-is.
    return str(value)
