"""Tiferet Compiler Semantic Analysis Mapper Objects"""

# *** imports

# ** core
from typing import Optional

# ** app
from ..domain.semantic import SymbolKind, Symbol, Scope

# *** mappers

# ** mapper: scope_aggregate
class ScopeAggregate(Scope):
    """Aggregate extending Scope with static factories and mutation methods for building symbol tables."""

    # * method: new_module_scope (static)
    @staticmethod
    def new_module_scope(module_name: str) -> 'ScopeAggregate':
        """
        Create the root module scope.

        :param module_name: The name of the source module.
        :type module_name: str
        :return: A new ScopeAggregate representing the module scope.
        :rtype: ScopeAggregate
        """

        return ScopeAggregate(
            name='module',
            kind=SymbolKind.MODULE,
            path='module',
        )

    # * method: new_class_scope (static)
    @staticmethod
    def new_class_scope(name: str, parent_path: str) -> 'ScopeAggregate':
        """
        Create a class scope.

        :param name: The class name.
        :type name: str
        :param parent_path: The fully qualified path of the parent scope.
        :type parent_path: str
        :return: A new ScopeAggregate representing the class scope.
        :rtype: ScopeAggregate
        """

        return ScopeAggregate(
            name=name,
            kind=SymbolKind.CLASS_DEF,
            path=f'{parent_path}.{name}',
            parent_path=parent_path,
        )

    # * method: new_method_scope (static)
    @staticmethod
    def new_method_scope(name: str, parent_path: str) -> 'ScopeAggregate':
        """
        Create a method scope.

        :param name: The method name.
        :type name: str
        :param parent_path: The fully qualified path of the parent scope.
        :type parent_path: str
        :return: A new ScopeAggregate representing the method scope.
        :rtype: ScopeAggregate
        """

        return ScopeAggregate(
            name=name,
            kind=SymbolKind.METHOD,
            path=f'{parent_path}.{name}',
            parent_path=parent_path,
        )

    # * method: add_symbol
    def add_symbol(self, symbol: Symbol) -> None:
        """
        Add a symbol to this scope's symbols dict.

        :param symbol: The symbol to add.
        :type symbol: Symbol
        """

        self.symbols[symbol.name] = symbol

    # * method: add_child
    def add_child(self, name: str, child_path: str) -> None:
        """
        Register a child scope path in this scope's children dict.

        :param name: The name of the child scope.
        :type name: str
        :param child_path: The fully qualified path of the child scope.
        :type child_path: str
        """

        self.children[name] = child_path

    # * method: remove_child
    def remove_child(self, name: str) -> None:
        """
        Remove a child scope by name.

        :param name: The name of the child scope to remove.
        :type name: str
        """

        self.children.pop(name, None)

    # * method: has_symbol
    def has_symbol(self, name: str) -> bool:
        """
        Check if a symbol exists in this scope.

        :param name: The symbol name to check.
        :type name: str
        :return: True if the symbol exists, False otherwise.
        :rtype: bool
        """

        return name in self.symbols

    # * method: get_symbol
    def get_symbol(self, name: str) -> Optional[Symbol]:
        """
        Retrieve a symbol by name, or None if not found.

        :param name: The symbol name to look up.
        :type name: str
        :return: The Symbol if found, None otherwise.
        :rtype: Optional[Symbol]
        """

        return self.symbols.get(name)
