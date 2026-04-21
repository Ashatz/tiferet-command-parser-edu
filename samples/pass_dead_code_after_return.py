"""An event that demonstrates return-analysis: statements that appear
after a ``return`` within the same scope are flagged by the compiler
as unreachable code. This sample keeps the pattern simple -- a direct
post-return statement in two different method scopes -- to stay inside
what the parser's INDENT/DEDENT injection currently supports."""

# *** imports

# ** infra
from tiferet.events import DomainEvent

# *** events

# ** event: classify_score
class ClassifyScore(DomainEvent):
    """Classify a score with intentionally unreachable trailing code."""

    # * method: execute
    def execute(self, score: int, **kwargs) -> str:
        """Classify the score.

        :param score: The score to classify.
        :type score: int
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: A classification label.
        :rtype: str
        """

        # Return the label immediately.
        return 'score recorded'

        # This statement is unreachable because it follows a return
        # within the same scope, and the compiler flags it as
        # UNREACHABLE_AFTER_RETURN.
        note = 'never reached'

    # * method: describe
    def describe(self, label: str, **kwargs) -> str:
        """Describe a label with two unreachable trailing statements.

        :param label: The label to describe.
        :type label: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: A description string.
        :rtype: str
        """

        # Return the decorated label immediately.
        return 'label: ' + label

        # The following two statements both sit on the same post-return
        # chain and are flagged as UNREACHABLE_AFTER_RETURN in order.
        trailing = 'trailing assignment'
        extra = 'another trailing assignment'
