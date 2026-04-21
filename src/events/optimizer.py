"""Optimization Domain Events"""

# *** imports

# ** core
from typing import Any, Dict

# ** app
from ..interfaces.optimizer import (
    ASTOptimizerService,
    ASTStrengthReducerService,
    OptimizerService,
)
from ..mappers import Decl
from .settings import DomainEvent

# *** events

# ** event: fold_constants
class FoldConstants(DomainEvent):
    '''
    AST optimization event that folds constant arithmetic sub-expressions
    before IR generation.  Delegates the walk to the injected
    ASTOptimizerService, returning the optimized AST root.
    '''

    # * attribute: ast_optimizer_service
    ast_optimizer_service: ASTOptimizerService

    # * init
    def __init__(self, ast_optimizer_service: ASTOptimizerService):
        '''
        Initialize with an injected AST optimizer service.

        :param ast_optimizer_service: The AST optimization service to apply.
        :type ast_optimizer_service: ASTOptimizerService
        '''

        # Set the AST optimizer service dependency.
        self.ast_optimizer_service = ast_optimizer_service

    # * method: execute
    @DomainEvent.parameters_required(['ast'])
    def execute(self,
            ast: Decl,
            O: str = 'O1',
            **kwargs,
        ) -> Decl:
        '''
        Apply the AST constant-folding pass based on the optimization level.
        O0 passes through unchanged; O1 or higher applies constant folding.
        Defaults to O1 so that the IR pipeline always folds unless told otherwise.

        :param ast: The parsed module DeclarationAggregate.
        :type ast: Decl
        :param O: Optimization level (O0, O1, O2, ...).
        :type O: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The AST root, folded at O1+ or unchanged at O0.
        :rtype: Decl
        '''

        # Normalize the optimization level.
        level = O.strip().upper() if O else 'O1'

        # O0: pass through unchanged.
        if level == 'O0':
            return ast

        # O1 or higher: fold constant arithmetic sub-expressions.
        return self.ast_optimizer_service.fold(ast)


# ** event: reduce_strength
class ReduceStrength(DomainEvent):
    '''
    AST optimization event that applies strength reduction to
    arithmetic sub-expressions before IR generation. Delegates the
    walk to the injected ASTStrengthReducerService, returning the
    optimized AST root.
    '''

    # * attribute: ast_strength_reducer_service
    ast_strength_reducer_service: ASTStrengthReducerService

    # * init
    def __init__(self, ast_strength_reducer_service: ASTStrengthReducerService):
        '''
        Initialize with an injected AST strength reducer service.

        :param ast_strength_reducer_service: The strength reduction service to apply.
        :type ast_strength_reducer_service: ASTStrengthReducerService
        '''

        # Set the AST strength reducer service dependency.
        self.ast_strength_reducer_service = ast_strength_reducer_service

    # * method: execute
    @DomainEvent.parameters_required(['ast'])
    def execute(self,
            ast: Decl,
            O: str = 'O1',
            **kwargs,
        ) -> Decl:
        '''
        Apply the AST strength-reduction pass based on the optimization
        level. O0 passes through unchanged; O1 or higher applies the
        rewriter. Defaults to O1 so the IR pipeline always reduces
        unless told otherwise.

        :param ast: The parsed module DeclarationAggregate.
        :type ast: Decl
        :param O: Optimization level (O0, O1, O2, ...).
        :type O: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The AST root, reduced at O1+ or unchanged at O0.
        :rtype: Decl
        '''

        # Normalize the optimization level.
        level = O.strip().upper() if O else 'O1'

        # O0: pass through unchanged.
        if level == 'O0':
            return ast

        # O1 or higher: apply strength reduction.
        return self.ast_strength_reducer_service.reduce(ast)


# ** event: optimize_code
class OptimizeCode(DomainEvent):
    '''
    Optimization event that deduplicates repeated structures in the codegen
    output dict, enabling YAML anchor/alias emission.
    '''

    # * attribute: optimizer_service
    optimizer_service: OptimizerService

    # * init
    def __init__(self, optimizer_service: OptimizerService):
        '''
        Initialize with injected optimizer service.

        :param optimizer_service: The optimizer service.
        :type optimizer_service: OptimizerService
        '''

        # Set the optimizer service dependency.
        self.optimizer_service = optimizer_service

    # * method: execute
    @DomainEvent.parameters_required(['codegen'])
    def execute(self,
            codegen: Dict[str, Any],
            O: str = 'O0',
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Optimize the codegen dict based on the requested optimization level.
        O0 and O1 pass through unchanged; O2 applies YAML anchor/alias deduplication.

        :param codegen: The codegen output dict from GenerateCode.
        :type codegen: Dict[str, Any]
        :param O: Optimization level (O0, O1, O2, ...).
        :type O: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The optimized or original codegen dict.
        :rtype: Dict[str, Any]
        '''

        # Normalize the optimization level.
        level = O.strip().upper() if O else 'O0'

        # O0 or O1: pass through unchanged.
        if level in ('O0', 'O1'):
            return codegen

        # O2 or higher: YAML anchor/alias deduplication.
        if level >= 'O2':
            codegen = self.optimizer_service.optimize(codegen)

        # Return the optimized dict.
        return codegen
