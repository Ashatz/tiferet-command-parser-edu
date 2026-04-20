"""Semantic Analysis Domain Events"""

# *** imports

# ** core
from typing import Dict, Any

# ** app
from ..mappers import Decl
from ..utils import SymbolTableBuilder, NameResolver
from .settings import DomainEvent, a

# *** events

# ** event: perform_semantic_analysis
class PerformSemanticAnalysis(DomainEvent):
    '''
    Core analytical event that performs semantic analysis on the
    parsed AST, building a symbol table and resolving name references.
    '''

    # * method: execute
    @DomainEvent.parameters_required(['ast'])
    def execute(self,
            ast: Decl,
            source_file: str = None,
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Build a symbol table from the AST and resolve name references.

        :param ast: The parsed AST DeclarationAggregate from PerformSyntacticAnalysis.
        :type ast: Decl
        :param source_file: The original source file path.
        :type source_file: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: Semantic analysis result with symbol_table and resolution.
        :rtype: Dict[str, Any]
        '''

        # Validate that the AST is a DeclarationAggregate.
        self.verify(
            expression=ast and isinstance(ast, Decl),
            error_code='INVALID_AST_STRUCTURE',
            message='Semantic analysis requires a valid Module AST',
            ast_type=str(type(ast)),
        )

        # Build the symbol table from the AST.
        builder = SymbolTableBuilder()
        symbol_table = builder.build(ast)

        # Resolve name references against the symbol table.
        resolver = NameResolver(builder.scopes)
        resolution = resolver.resolve(ast)

        # Return the semantic analysis result.
        return {
            'symbol_table': symbol_table,
            'resolution': resolution.model_dump(exclude_none=True),
        }
