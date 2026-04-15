"""Type Checking Domain Events"""

# *** imports

# ** core
from typing import List, Dict, Any

# ** app
from ..mappers import Decl
from ..utils.typecheck import TypeChecker
from ..mappers.semantic import ScopeAggregate
from .settings import DomainEvent, a

# *** events

# ** event: perform_type_check
class PerformTypeCheck(DomainEvent):
    '''
    Domain event that performs type checking against the symbol table.
    Takes the AST and semantic analysis result, runs the type checker,
    and returns a list of descriptive type errors.
    '''

    # * method: execute
    @DomainEvent.parameters_required(['ast', 'semantic'])
    def execute(self,
            ast: Decl,
            semantic: Dict[str, Any],
            **kwargs,
        ) -> List[Dict]:
        '''
        Run type checking over the AST using the symbol table from semantic analysis.

        :param ast: The parsed AST DeclarationAggregate.
        :type ast: Decl
        :param semantic: The semantic analysis result containing symbol_table with scopes.
        :type semantic: Dict[str, Any]
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: List of type error descriptors.
        :rtype: List[Dict]
        '''

        # Extract the symbol table from the semantic result.
        symbol_table = semantic.get('symbol_table', {})
        raw_scopes = symbol_table.get('scopes', {})

        # Reconstruct ScopeAggregate instances from the serialized scope data.
        scopes = {
            path: ScopeAggregate(**scope_data)
            for path, scope_data in raw_scopes.items()
        }

        # Run type checking against the AST.
        checker = TypeChecker(scopes)
        errors = checker.check(ast)

        # Return the list of type errors.
        return errors
