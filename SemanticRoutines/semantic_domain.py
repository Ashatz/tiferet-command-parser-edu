"""Tiferet Compiler Semantic Analysis Domain Objects"""

# *** imports

# ** core
from enum import Enum
from typing import Optional, List, Dict

# ** infra
from pydantic import BaseModel, Field

# *** enums

# ** enum: symbol_kind
class SymbolKind(str, Enum):
    '''Enumeration of valid symbol kinds in the Tiferet symbol table.'''

    MODULE = 'module'
    IMPORT = 'import'
    CLASS_DEF = 'class_def'
    METHOD = 'method'
    ATTRIBUTE = 'attribute'
    PARAMETER = 'parameter'
    VARIABLE = 'variable'

# *** objects

# ** object: symbol
class Symbol(BaseModel):
    """A symbol entry in the Tiferet symbol table, representing a named entity (import, class, method, attribute, parameter, or variable)."""

    # * attribute: name
    name: str = Field(
        ...,
        description='The symbol name.'
    )

    # * attribute: kind
    kind: SymbolKind = Field(
        ...,
        description='What the symbol represents (e.g., import, class_def, method).'
    )

    # * attribute: type_annotation
    type_annotation: Optional[str] = Field(
        None,
        description='Lightweight type hint string (e.g., "str", "int", "DomainEvent"). Recorded for reference, not used for type checking.'
    )

    # * attribute: scope_path
    scope_path: str = Field(
        ...,
        description='Fully qualified scope path where this symbol is defined (e.g., "module", "module.Ping", "module.Ping.execute").'
    )

    # * attribute: source_module
    source_module: Optional[str] = Field(
        None,
        description='For imports: the module path (e.g., ".settings", "typing").'
    )

# ** object: scope
class Scope(BaseModel):
    """A lexical scope in the Tiferet symbol table, representing a module, class, or method scope."""

    # * attribute: name
    name: str = Field(
        ...,
        description='Scope segment name (e.g., "module", "Ping", "execute").'
    )

    # * attribute: kind
    kind: SymbolKind = Field(
        ...,
        description='The kind of scope (module, class_def, or method).'
    )

    # * attribute: path
    path: str = Field(
        ...,
        description='Fully qualified path (e.g., "module.Ping.execute").'
    )

    # * attribute: symbols
    symbols: Dict[str, Symbol] = Field(
        default_factory=dict,
        description='Name to Symbol map for this scope.'
    )

    # * attribute: children
    children: Dict[str, str] = Field(
        default_factory=dict,
        description='Name to child scope path map.'
    )

    # * attribute: parent_path
    parent_path: Optional[str] = Field(
        None,
        description='Path of the parent scope (None for module).'
    )

# ** object: resolved_name
class ResolvedName(BaseModel):
    """A successfully resolved name reference."""

    # * attribute: name
    name: str = Field(
        ...,
        description='The name that was resolved.'
    )

    # * attribute: scope_path
    scope_path: str = Field(
        ...,
        description='The scope path where the name reference was encountered.'
    )

    # * attribute: resolved_to
    resolved_to: str = Field(
        ...,
        description='The scope path where the symbol definition was found.'
    )

# ** object: unresolved_name
class UnresolvedName(BaseModel):
    """A name reference that could not be resolved."""

    # * attribute: name
    name: str = Field(
        ...,
        description='The name that could not be resolved.'
    )

    # * attribute: scope_path
    scope_path: str = Field(
        ...,
        description='The scope path where the unresolved name reference was encountered.'
    )

# ** object: resolution_result
class ResolutionResult(BaseModel):
    """The result of name resolution across the entire AST."""

    # * attribute: resolved
    resolved: List[ResolvedName] = Field(
        default_factory=list,
        description='Successfully resolved name references.'
    )

    # * attribute: unresolved
    unresolved: List[UnresolvedName] = Field(
        default_factory=list,
        description='Name references that could not be resolved.'
    )
