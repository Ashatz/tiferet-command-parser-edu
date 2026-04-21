"""Optimizer Service Interfaces"""

# *** imports

# ** core
from abc import abstractmethod
from typing import Any, Dict

# ** infra
from tiferet.interfaces.settings import Service

# ** app
from ..domain.ast import Declaration

# *** interfaces

# ** interface: optimizer_service
class OptimizerService(Service):
    '''
    Abstract interface for optimizing codegen output with YAML anchors/aliases.
    '''

    # * method: optimize
    @abstractmethod
    def optimize(self, codegen: Dict[str, Any]) -> Dict[str, Any]:
        '''
        Optimize a codegen output dict by sharing repeated structures
        so that PyYAML emits anchors and aliases automatically.

        :param codegen: The codegen output dict from TiferetGenerator.
        :type codegen: Dict[str, Any]
        :return: The optimized dict with shared object references.
        :rtype: Dict[str, Any]
        '''

        raise NotImplementedError()


# ** interface: ast_optimizer_service
class ASTOptimizerService(Service):
    '''
    Abstract interface for AST-level optimization passes.
    Implementations walk the parsed AST and return a (potentially
    mutated) AST root that has been optimized before IR generation.
    '''

    # * method: fold
    @abstractmethod
    def fold(self, ast: Declaration) -> Declaration:
        '''
        Walk the AST rooted at *ast* and apply optimizations in place,
        returning the (possibly replaced) root node.

        :param ast: The root DeclarationAggregate produced by the parser.
        :type ast: Declaration
        :return: The optimized AST root.
        :rtype: Declaration
        '''

        raise NotImplementedError()


# ** interface: ast_strength_reducer_service
class ASTStrengthReducerService(Service):
    '''
    Abstract interface for AST-level strength reduction passes.
    Implementations walk the parsed AST and rewrite expensive
    arithmetic operations (multiplication/division by a power of two,
    exponentiation by two) into cheaper equivalents (shifts,
    self-multiplication).
    '''

    # * method: reduce
    @abstractmethod
    def reduce(self, ast: Declaration) -> Declaration:
        '''
        Walk the AST rooted at *ast* and rewrite arithmetic
        sub-expressions where strength reduction applies, returning
        the (possibly replaced) root node.

        :param ast: The root DeclarationAggregate produced by the parser.
        :type ast: Declaration
        :return: The strength-reduced AST root.
        :rtype: Declaration
        '''

        raise NotImplementedError()
