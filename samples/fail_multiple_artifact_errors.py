# *** imports

# ** infra_bad
from typing import Any

# ** app
from .settings import DomainEvent

# *** events

# ** event: add_feature
class AddFeat(DomainEvent):
    """Class name AddFeat does not match expected AddFeature."""

    # * attribute: helper
    def helper(self) -> str:
        """Function under attribute member."""

        # Return help.
        return 'help'

    # * method: execute
    execute: str
