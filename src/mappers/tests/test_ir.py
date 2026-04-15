"""Mappers – IR Aggregate Tests"""

# *** imports

# ** infra
import pytest

# ** app
from ..ir import IREventGroupAggregate
from ...domain.ir import IREvent, IRImportGroup, IRImport, IRExecute

# *** fixtures

# ** fixture: empty_aggregate
@pytest.fixture
def empty_aggregate() -> IREventGroupAggregate:
    '''
    Returns an empty IREventGroupAggregate.

    :return: An IREventGroupAggregate with no events or import groups.
    :rtype: IREventGroupAggregate
    '''

    return IREventGroupAggregate(name='test_module', description='')


# ** fixture: sample_event
@pytest.fixture
def sample_event() -> IREvent:
    '''
    Returns a minimal IREvent for testing mutation.

    :return: A minimal IREvent.
    :rtype: IREvent
    '''

    return IREvent(artifact_name='test_event', class_name='TestEvent', doc_string='A test event.')


# ** fixture: sample_import_group
@pytest.fixture
def sample_import_group() -> IRImportGroup:
    '''
    Returns a minimal IRImportGroup for testing mutation.

    :return: An IRImportGroup with one import.
    :rtype: IRImportGroup
    '''

    return IRImportGroup(
        category='app',
        imports=[IRImport(module_path='.settings', symbol='DomainEvent')],
    )


# *** tests

# ** test: aggregate_add_event
def test_aggregate_add_event(
        empty_aggregate: IREventGroupAggregate,
        sample_event: IREvent,
    ) -> None:
    '''
    Test that add_event appends an IREvent to the events collection.

    :param empty_aggregate: The aggregate to mutate.
    :type empty_aggregate: IREventGroupAggregate
    :param sample_event: The event to add.
    :type sample_event: IREvent
    '''

    # Verify the aggregate starts empty.
    assert len(empty_aggregate.events.events) == 0

    # Add the event and verify.
    empty_aggregate.add_event(sample_event)
    assert len(empty_aggregate.events.events) == 1
    assert empty_aggregate.events.events[0].class_name == 'TestEvent'


# ** test: aggregate_add_import_group
def test_aggregate_add_import_group(
        empty_aggregate: IREventGroupAggregate,
        sample_import_group: IRImportGroup,
    ) -> None:
    '''
    Test that add_import_group appends an IRImportGroup to the import groups.

    :param empty_aggregate: The aggregate to mutate.
    :type empty_aggregate: IREventGroupAggregate
    :param sample_import_group: The import group to add.
    :type sample_import_group: IRImportGroup
    '''

    # Verify the aggregate starts with no import groups.
    assert len(empty_aggregate.import_groups.groups) == 0

    # Add the group and verify.
    empty_aggregate.add_import_group(sample_import_group)
    assert len(empty_aggregate.import_groups.groups) == 1
    assert empty_aggregate.import_groups.groups[0].category == 'app'


# ** test: aggregate_add_multiple_events
def test_aggregate_add_multiple_events(
        empty_aggregate: IREventGroupAggregate,
    ) -> None:
    '''
    Test that multiple events can be added to the aggregate in order.

    :param empty_aggregate: The aggregate to mutate.
    :type empty_aggregate: IREventGroupAggregate
    '''

    # Add two events.
    empty_aggregate.add_event(IREvent(artifact_name='add', class_name='Add', doc_string=''))
    empty_aggregate.add_event(IREvent(artifact_name='subtract', class_name='Subtract', doc_string=''))

    # Verify order and count.
    assert len(empty_aggregate.events.events) == 2
    assert empty_aggregate.events.events[0].class_name == 'Add'
    assert empty_aggregate.events.events[1].class_name == 'Subtract'


# ** test: aggregate_to_keter_after_mutation
def test_aggregate_to_keter_after_mutation(
        empty_aggregate: IREventGroupAggregate,
        sample_event: IREvent,
        sample_import_group: IRImportGroup,
    ) -> None:
    '''
    Test that the keter output reflects mutations made via add_event and add_import_group.

    :param empty_aggregate: The aggregate to mutate.
    :type empty_aggregate: IREventGroupAggregate
    :param sample_event: The event to add.
    :type sample_event: IREvent
    :param sample_import_group: The import group to add.
    :type sample_import_group: IRImportGroup
    '''

    # Mutate the aggregate.
    empty_aggregate.add_import_group(sample_import_group)
    empty_aggregate.add_event(sample_event)

    # Verify keter output contains both added items.
    keter = empty_aggregate.to_keter()
    assert 'ImportGroup(app' in keter
    assert 'Event(test_event, TestEvent' in keter
