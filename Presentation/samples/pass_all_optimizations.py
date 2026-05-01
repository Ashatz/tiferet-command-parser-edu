"""Four events demonstrating each compiler optimization.
The shared signature across all events triggers YAML anchor/alias at -O O2."""

# *** imports

# ** infra
from tiferet.events import DomainEvent

# *** events

# ** event: fold_constants
class FoldConstants(DomainEvent):
    """Constant Folding: pure-literal sub-expressions evaluated at compile time."""

    # * method: execute
    def execute(self, value: int, **kwargs) -> int:
        """Return value adjusted by two folded constants.

        :param value: The input value.
        :type value: int
        :return: The folded result.
        :rtype: int
        """

        # (3 * 5) folds to 15 and (2 + 6) folds to 8 at compile time.
        return value + (3 * 5) - (2 + 6)

# ** event: reduce_strength
class ReduceStrength(DomainEvent):
    """Strength Reduction: power-of-two ops rewritten to cheaper bit shifts."""

    # * method: execute
    def execute(self, value: int, **kwargs) -> int:
        """Return three strength-reduced values combined.

        :param value: The input value.
        :type value: int
        :return: The combined result.
        :rtype: int
        """

        # value * 8  ->  value << 3  (multiply by 2**3 becomes left shift)
        scaled = value * 8

        # value / 4  ->  value >> 2  (divide by 2**2 becomes right shift)
        halved = value / 4

        # value ** 2  ->  value * value  (squaring becomes self-multiplication)
        squared = value ** 2

        # Return the combined result.
        return scaled + halved + squared

# ** event: eliminate_dead_code
class EliminateDeadCode(DomainEvent):
    """Dead Code Elimination: unreachable statements removed from the AST."""

    # * method: execute
    def execute(self, value: int, **kwargs) -> int:
        """Return the value immediately.

        :param value: The input value.
        :type value: int
        :return: The input value plus one.
        :rtype: int
        """

        # Return immediately -- everything below this is unreachable.
        return value + 1

        # Flagged as UNREACHABLE_AFTER_RETURN and pruned from the AST at O1.
        unused = 'never reached'

# ** event: anchor_alias_dedup
class AnchorAliasDedup(DomainEvent):
    """Anchor/Alias Dedup: identical params and returns collapsed to YAML anchors."""

    # * method: execute
    def execute(self, value: int, **kwargs) -> int:
        """Return the value unchanged.

        :param value: The input value.
        :type value: int
        :return: The input value.
        :rtype: int
        """

        # All four events share (value: int) params and int return type.
        # At -O O2 the YAML optimizer emits one anchor and three aliases.
        return value
