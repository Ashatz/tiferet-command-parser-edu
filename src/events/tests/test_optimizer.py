"""Events – Optimizer Domain Event Tests"""

# *** imports

# ** core
from typing import Any, Dict
from unittest import mock

# ** infra
import pytest
from tiferet.events import TiferetError, DomainEvent

# ** app
from ...domain.ast import ExprKind, StatementKind
from ...interfaces.optimizer import (
    ASTOptimizerService,
    ASTStrengthReducerService,
    OptimizerService,
)
from ...mappers.ast import ExpressionAggregate, StatementAggregate, DeclarationAggregate
from ...utils.optimizer import ConstantFolder, StrengthReducer
from ..optimizer import FoldConstants, OptimizeCode, ReduceStrength

# *** fixtures

# ** fixture: mock_ast_optimizer_service
@pytest.fixture
def mock_ast_optimizer_service() -> ASTOptimizerService:
    '''
    Returns a mock ASTOptimizerService for testing.

    :return: A mock ASTOptimizerService.
    :rtype: ASTOptimizerService
    '''

    return mock.Mock(spec=ASTOptimizerService)


# ** fixture: mock_ast_strength_reducer_service
@pytest.fixture
def mock_ast_strength_reducer_service() -> ASTStrengthReducerService:
    '''
    Returns a mock ASTStrengthReducerService for testing.

    :return: A mock ASTStrengthReducerService.
    :rtype: ASTStrengthReducerService
    '''

    return mock.Mock(spec=ASTStrengthReducerService)


# ** fixture: mock_optimizer_service
@pytest.fixture
def mock_optimizer_service() -> OptimizerService:
    '''
    Returns a mock OptimizerService for testing.

    :return: A mock OptimizerService.
    :rtype: OptimizerService
    '''

    return mock.Mock(spec=OptimizerService)


# ** fixture: sample_ast
@pytest.fixture
def sample_ast() -> DeclarationAggregate:
    '''
    Returns a minimal module DeclarationAggregate for testing.

    :return: A sample DeclarationAggregate.
    :rtype: DeclarationAggregate
    '''

    return DeclarationAggregate(name='test_module')


# ** fixture: sample_codegen_output
@pytest.fixture
def sample_codegen_output() -> Dict[str, Any]:
    '''
    Returns a minimal codegen output dict for testing.

    :return: A sample codegen dict.
    :rtype: Dict[str, Any]
    '''

    return {'evt_grp': {'name': 'test_module'}}


# *** tests — FoldConstants

# ** test: fold_constants_delegates_to_service
def test_fold_constants_delegates_to_service(
        mock_ast_optimizer_service: ASTOptimizerService,
        sample_ast: DeclarationAggregate,
    ) -> None:
    '''
    Test that FoldConstants calls ast_optimizer_service.fold and returns the result.

    :param mock_ast_optimizer_service: The mock AST optimizer service.
    :type mock_ast_optimizer_service: ASTOptimizerService
    :param sample_ast: The sample AST root.
    :type sample_ast: DeclarationAggregate
    '''

    # Arrange the service to return the same AST root.
    mock_ast_optimizer_service.fold.return_value = sample_ast

    # Execute via DomainEvent.handle.
    result = DomainEvent.handle(
        FoldConstants,
        dependencies={'ast_optimizer_service': mock_ast_optimizer_service},
        ast=sample_ast,
    )

    # Assert the result is the returned AST and the service was called once.
    assert result is sample_ast
    mock_ast_optimizer_service.fold.assert_called_once_with(sample_ast)


# ** test: fold_constants_o0_passthrough
def test_fold_constants_o0_passthrough(
        mock_ast_optimizer_service: ASTOptimizerService,
        sample_ast: DeclarationAggregate,
    ) -> None:
    '''
    Test that FoldConstants at O0 returns the AST unchanged without calling the service.

    :param mock_ast_optimizer_service: The mock AST optimizer service.
    :type mock_ast_optimizer_service: ASTOptimizerService
    :param sample_ast: The sample AST root.
    :type sample_ast: DeclarationAggregate
    '''

    # Execute at O0.
    result = DomainEvent.handle(
        FoldConstants,
        dependencies={'ast_optimizer_service': mock_ast_optimizer_service},
        ast=sample_ast,
        O='O0',
    )

    # The original AST must be returned and the service must not be called.
    assert result is sample_ast
    mock_ast_optimizer_service.fold.assert_not_called()


# ** test: fold_constants_missing_ast
def test_fold_constants_missing_ast(
        mock_ast_optimizer_service: ASTOptimizerService,
    ) -> None:
    '''
    Test that FoldConstants raises TiferetError when ast is not provided.

    :param mock_ast_optimizer_service: The mock AST optimizer service.
    :type mock_ast_optimizer_service: ASTOptimizerService
    '''

    with pytest.raises(TiferetError):
        DomainEvent.handle(
            FoldConstants,
            dependencies={'ast_optimizer_service': mock_ast_optimizer_service},
            # ast intentionally omitted
        )


# ** test: fold_constants_with_real_folder
def test_fold_constants_with_real_folder(sample_ast: DeclarationAggregate) -> None:
    '''
    Integration test: FoldConstants using the real ConstantFolder service
    folds a constant expression embedded in a return statement.

    :param sample_ast: The sample AST root (will have a return statement added).
    :type sample_ast: DeclarationAggregate
    '''

    # Embed a constant return expression: return 3 * 5
    const_expr = ExpressionAggregate(
        kind=ExprKind.MUL,
        left=ExpressionAggregate(kind=ExprKind.INT_VAL, value='3'),
        right=ExpressionAggregate(kind=ExprKind.INT_VAL, value='5'),
    )
    sample_ast.code = StatementAggregate(kind=StatementKind.RETURN, expr=const_expr)

    # Execute with the real ConstantFolder.
    result = DomainEvent.handle(
        FoldConstants,
        dependencies={'ast_optimizer_service': ConstantFolder()},
        ast=sample_ast,
    )

    # The return expression should now be INT_VAL 15.
    assert result.code.expr.kind == ExprKind.INT_VAL
    assert result.code.expr.value == '15'


# *** tests — OptimizeCode

# ** test: optimize_code_o0_passthrough
def test_optimize_code_o0_passthrough(
        mock_optimizer_service: OptimizerService,
        sample_codegen_output: Dict[str, Any],
    ) -> None:
    '''
    Test that OptimizeCode at O0 returns the codegen dict unchanged.

    :param mock_optimizer_service: The mock optimizer service.
    :type mock_optimizer_service: OptimizerService
    :param sample_codegen_output: The sample codegen dict.
    :type sample_codegen_output: Dict[str, Any]
    '''

    # Execute at O0.
    result = DomainEvent.handle(
        OptimizeCode,
        dependencies={'optimizer_service': mock_optimizer_service},
        codegen=sample_codegen_output,
        O='O0',
    )

    # The service must not be called and the dict must be returned unchanged.
    assert result is sample_codegen_output
    mock_optimizer_service.optimize.assert_not_called()


# ** test: optimize_code_o1_passthrough
def test_optimize_code_o1_passthrough(
        mock_optimizer_service: OptimizerService,
        sample_codegen_output: Dict[str, Any],
    ) -> None:
    '''
    Test that OptimizeCode at O1 also passes through unchanged (O1 is reserved
    for AST constant folding only).

    :param mock_optimizer_service: The mock optimizer service.
    :type mock_optimizer_service: OptimizerService
    :param sample_codegen_output: The sample codegen dict.
    :type sample_codegen_output: Dict[str, Any]
    '''

    # Execute at O1.
    result = DomainEvent.handle(
        OptimizeCode,
        dependencies={'optimizer_service': mock_optimizer_service},
        codegen=sample_codegen_output,
        O='O1',
    )

    # At O1, YAML deduplication must not be applied.
    assert result is sample_codegen_output
    mock_optimizer_service.optimize.assert_not_called()


# ** test: optimize_code_o2_delegates_to_service
def test_optimize_code_o2_delegates_to_service(
        mock_optimizer_service: OptimizerService,
        sample_codegen_output: Dict[str, Any],
    ) -> None:
    '''
    Test that OptimizeCode at O2 calls optimizer_service.optimize.

    :param mock_optimizer_service: The mock optimizer service.
    :type mock_optimizer_service: OptimizerService
    :param sample_codegen_output: The sample codegen dict.
    :type sample_codegen_output: Dict[str, Any]
    '''

    # Arrange the service to return the same dict.
    mock_optimizer_service.optimize.return_value = sample_codegen_output

    # Execute at O2.
    result = DomainEvent.handle(
        OptimizeCode,
        dependencies={'optimizer_service': mock_optimizer_service},
        codegen=sample_codegen_output,
        O='O2',
    )

    # Assert the service was called and the result is the optimized dict.
    assert result is sample_codegen_output
    mock_optimizer_service.optimize.assert_called_once_with(sample_codegen_output)


# ** test: optimize_code_missing_codegen
def test_optimize_code_missing_codegen(
        mock_optimizer_service: OptimizerService,
    ) -> None:
    '''
    Test that OptimizeCode raises TiferetError when codegen is not provided.

    :param mock_optimizer_service: The mock optimizer service.
    :type mock_optimizer_service: OptimizerService
    '''

    with pytest.raises(TiferetError):
        DomainEvent.handle(
            OptimizeCode,
            dependencies={'optimizer_service': mock_optimizer_service},
            # codegen intentionally omitted
        )


# ** test: reduce_strength_delegates_to_service
def test_reduce_strength_delegates_to_service(
        mock_ast_strength_reducer_service: ASTStrengthReducerService,
        sample_ast: DeclarationAggregate,
    ) -> None:
    '''
    Test that ReduceStrength calls ast_strength_reducer_service.reduce and
    returns the result.

    :param mock_ast_strength_reducer_service: The mock strength reducer service.
    :type mock_ast_strength_reducer_service: ASTStrengthReducerService
    :param sample_ast: The sample AST root.
    :type sample_ast: DeclarationAggregate
    '''

    # Arrange the service to return the same AST root.
    mock_ast_strength_reducer_service.reduce.return_value = sample_ast

    # Execute via DomainEvent.handle.
    result = DomainEvent.handle(
        ReduceStrength,
        dependencies={'ast_strength_reducer_service': mock_ast_strength_reducer_service},
        ast=sample_ast,
    )

    # Assert the result is the returned AST and the service was called once.
    assert result is sample_ast
    mock_ast_strength_reducer_service.reduce.assert_called_once_with(sample_ast)


# ** test: reduce_strength_o0_passthrough
def test_reduce_strength_o0_passthrough(
        mock_ast_strength_reducer_service: ASTStrengthReducerService,
        sample_ast: DeclarationAggregate,
    ) -> None:
    '''
    Test that ReduceStrength at O0 returns the AST unchanged without calling
    the service.

    :param mock_ast_strength_reducer_service: The mock strength reducer service.
    :type mock_ast_strength_reducer_service: ASTStrengthReducerService
    :param sample_ast: The sample AST root.
    :type sample_ast: DeclarationAggregate
    '''

    # Execute at O0.
    result = DomainEvent.handle(
        ReduceStrength,
        dependencies={'ast_strength_reducer_service': mock_ast_strength_reducer_service},
        ast=sample_ast,
        O='O0',
    )

    # The original AST must be returned and the service must not be called.
    assert result is sample_ast
    mock_ast_strength_reducer_service.reduce.assert_not_called()


# ** test: reduce_strength_missing_ast
def test_reduce_strength_missing_ast(
        mock_ast_strength_reducer_service: ASTStrengthReducerService,
    ) -> None:
    '''
    Test that ReduceStrength raises TiferetError when ast is not provided.

    :param mock_ast_strength_reducer_service: The mock strength reducer service.
    :type mock_ast_strength_reducer_service: ASTStrengthReducerService
    '''

    with pytest.raises(TiferetError):
        DomainEvent.handle(
            ReduceStrength,
            dependencies={'ast_strength_reducer_service': mock_ast_strength_reducer_service},
            # ast intentionally omitted
        )


# ** test: reduce_strength_with_real_reducer
def test_reduce_strength_with_real_reducer(sample_ast: DeclarationAggregate) -> None:
    '''
    Integration test: ReduceStrength using the real StrengthReducer service
    rewrites a constant-power-of-two multiplication embedded in a return.

    :param sample_ast: The sample AST root (will have a return statement added).
    :type sample_ast: DeclarationAggregate
    '''

    # Embed: return x * 8.
    mul_expr = ExpressionAggregate(
        kind=ExprKind.MUL,
        left=ExpressionAggregate(kind=ExprKind.NAME, name='x'),
        right=ExpressionAggregate(kind=ExprKind.INT_VAL, value='8'),
    )
    sample_ast.code = StatementAggregate(kind=StatementKind.RETURN, expr=mul_expr)

    # Execute with the real StrengthReducer.
    result = DomainEvent.handle(
        ReduceStrength,
        dependencies={'ast_strength_reducer_service': StrengthReducer()},
        ast=sample_ast,
    )

    # The return expression should now be a SHL node: x << 3.
    reduced = result.code.expr
    assert reduced.kind == ExprKind.SHL
    assert reduced.left.name == 'x'
    assert reduced.right.kind == ExprKind.INT_VAL
    assert reduced.right.value == '3'
