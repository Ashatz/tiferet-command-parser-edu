"""Tests for Symbol Table Mapper Objects"""

# *** imports

# ** infra
import pytest

# ** app
from ...domain.symbol import SymbolKind, Symbol
from ..symbol import ScopeAggregate

# *** tests

# ** test: new_module_scope
def test_new_module_scope():
    '''Verify new_module_scope factory produces correct path, kind, and empty state.'''

    scope = ScopeAggregate.new_module_scope('test_module')

    assert scope.name == 'module'
    assert scope.kind == SymbolKind.MODULE
    assert scope.path == 'module'
    assert scope.parent_path is None
    assert scope.symbols == {}
    assert scope.children == {}

# ** test: new_class_scope
def test_new_class_scope():
    '''Verify new_class_scope factory produces correct path from parent.'''

    scope = ScopeAggregate.new_class_scope('Ping', 'module')

    assert scope.name == 'Ping'
    assert scope.kind == SymbolKind.CLASS_DEF
    assert scope.path == 'module.Ping'
    assert scope.parent_path == 'module'

# ** test: new_method_scope
def test_new_method_scope():
    '''Verify new_method_scope factory produces correct path from parent.'''

    scope = ScopeAggregate.new_method_scope('execute', 'module.Ping')

    assert scope.name == 'execute'
    assert scope.kind == SymbolKind.METHOD
    assert scope.path == 'module.Ping.execute'
    assert scope.parent_path == 'module.Ping'

# ** test: add_symbol
def test_add_symbol():
    '''Verify add_symbol places symbol in scope's symbols dict.'''

    scope = ScopeAggregate.new_module_scope('test')
    symbol = Symbol(
        name='DomainEvent',
        kind=SymbolKind.IMPORT,
        scope_path='module',
        source_module='.settings',
    )

    scope.add_symbol(symbol)

    assert 'DomainEvent' in scope.symbols
    assert scope.symbols['DomainEvent'].kind == SymbolKind.IMPORT

# ** test: add_child
def test_add_child():
    '''Verify add_child registers a child scope path.'''

    scope = ScopeAggregate.new_module_scope('test')

    scope.add_child('Ping', 'module.Ping')

    assert scope.children == {'Ping': 'module.Ping'}

# ** test: remove_child
def test_remove_child():
    '''Verify remove_child removes a child scope by name.'''

    scope = ScopeAggregate.new_module_scope('test')
    scope.add_child('Ping', 'module.Ping')

    scope.remove_child('Ping')

    assert scope.children == {}

# ** test: remove_child_missing
def test_remove_child_missing():
    '''Verify remove_child is safe when name does not exist.'''

    scope = ScopeAggregate.new_module_scope('test')

    scope.remove_child('nonexistent')

    assert scope.children == {}

# ** test: has_symbol
def test_has_symbol():
    '''Verify has_symbol returns correct boolean.'''

    scope = ScopeAggregate.new_module_scope('test')
    symbol = Symbol(name='a', kind=SymbolKind.IMPORT, scope_path='module')

    assert scope.has_symbol('a') is False

    scope.add_symbol(symbol)

    assert scope.has_symbol('a') is True

# ** test: get_symbol
def test_get_symbol():
    '''Verify get_symbol returns symbol or None.'''

    scope = ScopeAggregate.new_module_scope('test')
    symbol = Symbol(name='pong', kind=SymbolKind.ATTRIBUTE, scope_path='module.Ping', type_annotation='str')

    assert scope.get_symbol('pong') is None

    scope.add_symbol(symbol)

    result = scope.get_symbol('pong')
    assert result is not None
    assert result.name == 'pong'
    assert result.type_annotation == 'str'
