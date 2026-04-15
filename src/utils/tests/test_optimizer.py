"""Utils – YamlAnchorOptimizer Tests"""

# *** imports

# ** infra
import pytest

# ** app
from ..optimizer import YamlAnchorOptimizer

# *** fixtures

# ** fixture: optimizer
@pytest.fixture
def optimizer() -> YamlAnchorOptimizer:
    '''
    Returns a fresh YamlAnchorOptimizer instance.

    :return: A YamlAnchorOptimizer.
    :rtype: YamlAnchorOptimizer
    '''

    return YamlAnchorOptimizer()


# ** fixture: no_events_codegen
@pytest.fixture
def no_events_codegen() -> dict:
    '''
    Returns a codegen dict with imports but no events.

    :return: A codegen dict without events.
    :rtype: dict
    '''

    return {
        'evt_grp': {
            'name': 'imports_only',
            'impt': {
                'app': [{'src': '.settings', 'tgts': ['DomainEvent']}],
            },
        }
    }


# ** fixture: single_event_codegen
@pytest.fixture
def single_event_codegen() -> dict:
    '''
    Returns a codegen dict with a single event.

    :return: A codegen dict with one event.
    :rtype: dict
    '''

    return {
        'evt_grp': {
            'name': 'single',
            'evts': {
                'ping': {
                    'name': 'Ping',
                    'execute': {
                        'params': ['kwargs:dict:false::'],
                        'returns': ['str:'],
                    },
                },
            },
        }
    }


# ** fixture: multiple_events_codegen
@pytest.fixture
def multiple_events_codegen() -> dict:
    '''
    Returns a codegen dict with multiple events sharing identical params/returns.

    :return: A codegen dict with repeated structures.
    :rtype: dict
    '''

    return {
        'evt_grp': {
            'name': 'operators',
            'evts': {
                'add': {
                    'name': 'Add',
                    'execute': {
                        'params': ['a:int:true::', 'b:int:true::'],
                        'returns': ['int:'],
                    },
                },
                'subtract': {
                    'name': 'Subtract',
                    'execute': {
                        'params': ['a:int:true::', 'b:int:true::'],
                        'returns': ['int:'],
                    },
                },
                'divide': {
                    'name': 'Divide',
                    'execute': {
                        'params': ['a:int:true::', 'b:int:true::'],
                        'returns': ['float:'],
                    },
                },
            },
        }
    }


# *** tests

# ** test: no_events_passthrough
def test_no_events_passthrough(optimizer: YamlAnchorOptimizer, no_events_codegen: dict) -> None:
    '''
    Test that a dict with no events returns unchanged with empty registry.

    :param optimizer: The optimizer instance.
    :type optimizer: YamlAnchorOptimizer
    :param no_events_codegen: A codegen dict without events.
    :type no_events_codegen: dict
    '''

    # Optimize the dict.
    result = optimizer.optimize(no_events_codegen)

    # Assert unchanged.
    assert result is no_events_codegen


# ** test: single_event_no_anchors
def test_single_event_no_anchors(optimizer: YamlAnchorOptimizer, single_event_codegen: dict) -> None:
    '''
    Test that a single event has nothing to deduplicate.

    :param optimizer: The optimizer instance.
    :type optimizer: YamlAnchorOptimizer
    :param single_event_codegen: A codegen dict with one event.
    :type single_event_codegen: dict
    '''

    # Optimize the dict.
    result = optimizer.optimize(single_event_codegen)

    # Assert no shared references created for single occurrences.
    assert result is single_event_codegen


# ** test: multiple_events_params_anchored
def test_multiple_events_params_anchored(optimizer: YamlAnchorOptimizer, multiple_events_codegen: dict) -> None:
    '''
    Test that identical params lists across events produce shared objects.

    :param optimizer: The optimizer instance.
    :type optimizer: YamlAnchorOptimizer
    :param multiple_events_codegen: A codegen dict with repeated params.
    :type multiple_events_codegen: dict
    '''

    # Optimize the dict.
    result = optimizer.optimize(multiple_events_codegen)
    evts = result['evt_grp']['evts']

    # All three events should share the same params list object.
    assert evts['add']['execute']['params'] is evts['subtract']['execute']['params']
    assert evts['add']['execute']['params'] is evts['divide']['execute']['params']

    # The shared object should also appear in vars.
    assert 'vars' in result
    assert evts['add']['execute']['params'] in result['vars']


# ** test: multiple_events_returns_anchored
def test_multiple_events_returns_anchored(optimizer: YamlAnchorOptimizer, multiple_events_codegen: dict) -> None:
    '''
    Test that identical returns lists produce shared objects.

    :param optimizer: The optimizer instance.
    :type optimizer: YamlAnchorOptimizer
    :param multiple_events_codegen: A codegen dict with repeated returns.
    :type multiple_events_codegen: dict
    '''

    # Optimize the dict.
    result = optimizer.optimize(multiple_events_codegen)
    evts = result['evt_grp']['evts']

    # Add and subtract share the same int returns.
    assert evts['add']['execute']['returns'] is evts['subtract']['execute']['returns']

    # Divide has a different returns (float) so it stays independent.
    assert evts['add']['execute']['returns'] is not evts['divide']['execute']['returns']

    # The shared int returns should appear in vars.
    assert evts['add']['execute']['returns'] in result['vars']


# ** test: vars_not_present_without_duplicates
def test_vars_not_present_without_duplicates(optimizer: YamlAnchorOptimizer, single_event_codegen: dict) -> None:
    '''
    Test that the vars key is not added when there are no repeated structures.

    :param optimizer: The optimizer instance.
    :type optimizer: YamlAnchorOptimizer
    :param single_event_codegen: A codegen dict with one event.
    :type single_event_codegen: dict
    '''

    # Optimize the dict.
    result = optimizer.optimize(single_event_codegen)

    # No vars section should be present.
    assert 'vars' not in result
