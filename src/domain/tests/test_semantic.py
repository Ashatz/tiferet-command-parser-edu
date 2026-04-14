"""Tests for Semantic Analysis Domain Objects"""

# *** imports

# ** infra
import pytest

# ** app
from ..semantic import SymbolKind, Symbol, Scope, ResolvedName, UnresolvedName, ResolutionResult

# *** tests

# ** test: symbol_kind_values
def test_symbol_kind_values():
    '''Verify all SymbolKind enum values are present and correct.'''

    assert SymbolKind.MODULE == 'module'
    assert SymbolKind.IMPORT == 'import'
    assert SymbolKind.CLASS_DEF == 'class_def'
    assert SymbolKind.METHOD == 'method'
    assert SymbolKind.ATTRIBUTE == 'attribute'
    assert SymbolKind.PARAMETER == 'parameter'
    assert SymbolKind.VARIABLE == 'variable'
    assert len(SymbolKind) == 7

# ** test: symbol_creation
def test_symbol_creation():
    '''Verify Symbol instantiation with all fields.'''

    symbol = Symbol(
        name='DomainEvent',
        kind=SymbolKind.IMPORT,
        type_annotation=None,
        scope_path='module',
        source_module='.settings',
    )

    assert symbol.name == 'DomainEvent'
    assert symbol.kind == SymbolKind.IMPORT
    assert symbol.scope_path == 'module'
    assert symbol.source_module == '.settings'
    assert symbol.type_annotation is None

# ** test: symbol_creation_with_type_annotation
def test_symbol_creation_with_type_annotation():
    '''Verify Symbol instantiation with a type annotation.'''

    symbol = Symbol(
        name='pong',
        kind=SymbolKind.ATTRIBUTE,
        type_annotation='str',
        scope_path='module.Ping',
    )

    assert symbol.name == 'pong'
    assert symbol.kind == SymbolKind.ATTRIBUTE
    assert symbol.type_annotation == 'str'
    assert symbol.source_module is None

# ** test: scope_creation
def test_scope_creation():
    '''Verify Scope instantiation with empty symbols and children.'''

    scope = Scope(
        name='module',
        kind=SymbolKind.MODULE,
        path='module',
    )

    assert scope.name == 'module'
    assert scope.kind == SymbolKind.MODULE
    assert scope.path == 'module'
    assert scope.symbols == {}
    assert scope.children == {}
    assert scope.parent_path is None

# ** test: scope_creation_with_parent
def test_scope_creation_with_parent():
    '''Verify Scope instantiation with a parent path.'''

    scope = Scope(
        name='Ping',
        kind=SymbolKind.CLASS_DEF,
        path='module.Ping',
        parent_path='module',
    )

    assert scope.parent_path == 'module'
    assert scope.path == 'module.Ping'

# ** test: resolved_name_creation
def test_resolved_name_creation():
    '''Verify ResolvedName instantiation.'''

    resolved = ResolvedName(
        name='DomainEvent',
        scope_path='module.Ping',
        resolved_to='module',
    )

    assert resolved.name == 'DomainEvent'
    assert resolved.scope_path == 'module.Ping'
    assert resolved.resolved_to == 'module'

# ** test: unresolved_name_creation
def test_unresolved_name_creation():
    '''Verify UnresolvedName instantiation.'''

    unresolved = UnresolvedName(
        name='missing_var',
        scope_path='module.Ping.execute',
    )

    assert unresolved.name == 'missing_var'
    assert unresolved.scope_path == 'module.Ping.execute'

# ** test: resolution_result_defaults
def test_resolution_result_defaults():
    '''Verify ResolutionResult defaults to empty lists.'''

    result = ResolutionResult()

    assert result.resolved == []
    assert result.unresolved == []

# ** test: resolution_result_with_entries
def test_resolution_result_with_entries():
    '''Verify ResolutionResult with resolved and unresolved entries.'''

    result = ResolutionResult(
        resolved=[
            ResolvedName(name='DomainEvent', scope_path='module.Ping', resolved_to='module'),
        ],
        unresolved=[
            UnresolvedName(name='missing', scope_path='module.Ping.execute'),
        ],
    )

    assert len(result.resolved) == 1
    assert len(result.unresolved) == 1
    assert result.resolved[0].name == 'DomainEvent'
    assert result.unresolved[0].name == 'missing'
