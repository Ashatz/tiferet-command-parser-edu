"""IR Mapper Objects"""

# *** imports

# ** app
from ..domain.ir import IREventGroup, IREvent, IRImportGroup

# *** mappers

# ** mapper: ir_event_group_aggregate
class IREventGroupAggregate(IREventGroup):
    '''
    Mutable aggregate for building an IREventGroup incrementally during IR generation.
    '''

    # * method: add_import_group
    def add_import_group(self, group: IRImportGroup) -> None:
        '''
        Append an import group to the import groups collection.

        :param group: The import group to add.
        :type group: IRImportGroup
        '''

        # Append the group to the import groups list.
        self.import_groups.groups.append(group)

    # * method: add_event
    def add_event(self, event: IREvent) -> None:
        '''
        Append an event to the events collection.

        :param event: The IR event to add.
        :type event: IREvent
        '''

        # Append the event to the events list.
        self.events.events.append(event)
