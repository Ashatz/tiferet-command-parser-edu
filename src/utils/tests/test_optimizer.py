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
    result, registry = optimizer.optimize(no_events_codegen)

    # Assert unchanged and empty registry.
    assert result is no_events_codegen
    assert registry == {}


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
    result, registry = optimizer.optimize(single_event_codegen)

    # Assert no anchors created for single occurrences.
    assert result is single_event_codegen
    assert registry == {}


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
    result, registry = optimizer.optimize(multiple_events_codegen)
    evts = result['evt_grp']['evts']

    # All three events should share the same params list object.
    assert evts['add']['execute']['params'] is evts['subtract']['execute']['params']
    assert evts['add']['execute']['params'] is evts['divide']['execute']['params']

    # The shared object should be in the registry.
    shared_params = evts['add']['execute']['params']
    assert id(shared_params) in registry
    assert 'params' in registry[id(shared_params)]


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
    result, registry = optimizer.optimize(multiple_events_codegen)
    evts = result['evt_grp']['evts']

    # Add and subtract share the same int returns.
    assert evts['add']['execute']['returns'] is evts['subtract']['execute']['returns']

    # Divide has a different returns (float) so it stays independent.
    assert evts['add']['execute']['returns'] is not evts['divide']['execute']['returns']


# ** test: mixed_returns_partial_anchor
def test_mixed_returns_partial_anchor(optimizer: YamlAnchorOptimizer, multiple_events_codegen: dict) -> None:
    '''
    Test that only repeated return types get anchored; unique ones stay independent.

    :param optimizer: The optimizer instance.
    :type optimizer: YamlAnchorOptimizer
    :param multiple_events_codegen: A codegen dict with mixed returns.
    :type multiple_events_codegen: dict
    '''

    # Optimize the dict.
    result, registry = optimizer.optimize(multiple_events_codegen)
    evts = result['evt_grp']['evts']

    # The int returns (add, subtract) should be anchored.
    int_returns = evts['add']['execute']['returns']
    assert id(int_returns) in registry

    # The float returns (divide only) should NOT be anchored.
    float_returns = evts['divide']['execute']['returns']
    assert id(float_returns) not in registry


# ** test: anchor_name_generation
def test_anchor_name_generation(optimizer: YamlAnchorOptimizer) -> None:
    '''
    Test that build_anchor_name produces meaningful names from content.

    :param optimizer: The optimizer instance.
    :type optimizer: YamlAnchorOptimizer
    '''

    # Test params anchor name.
    params_name = optimizer.build_anchor_name(
        ('a:int:true::', 'b:int:true::'), 'params',
    )
    assert params_name == 'int_a_b_params'

    # Test returns anchor name.
    returns_name = optimizer.build_anchor_name(
        ('int:',), 'returns',
    )
    assert returns_name == 'int_returns'

    # Test returns with description.
    returns_doc_name = optimizer.build_anchor_name(
        ('str:The result.',), 'returns',
    )
    assert returns_doc_name == 'str_returns'
