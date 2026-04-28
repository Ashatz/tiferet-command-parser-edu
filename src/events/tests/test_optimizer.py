"""Events – Optimizer Domain Event Tests"""

# *** imports

# ** core
from typing import Any, Dict
from unittest import mock

# ** infra
import pytest
from tiferet.events import TiferetError, DomainEvent

# ** app
from ...domain.ast import ExprKind, StatementKind, TypeKind
from ...interfaces.optimizer import (
    ASTOptimizerService,
    ASTStrengthReducerService,
    DeadCodeEliminatorService,
    OptimizerService,
    ReturnAnalyzerService,
)
from ...mappers.ast import (
    ExpressionAggregate,
    StatementAggregate,
    DeclarationAggregate,
    TypeAggregate,
)
from ...utils.optimizer import (
    ConstantFolder,
    DeadCodeEliminator,
    StrengthReducer,
    ReturnAnalyzer,
    UNREACHABLE_AFTER_RETURN_CODE,
)
from ..optimizer import (
    AnalyzeReturns,
    EliminateDeadCode,
    FoldConstants,
    OptimizeCode,
    ReduceStrength,
)

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


# ** fixture: mock_return_analyzer_service
@pytest.fixture
def mock_return_analyzer_service() -> ReturnAnalyzerService:
    '''
    Returns a mock ReturnAnalyzerService for testing.

    :return: A mock ReturnAnalyzerService.
    :rtype: ReturnAnalyzerService
    '''

    return mock.Mock(spec=ReturnAnalyzerService)


# ** test: analyze_returns_delegates_to_service
def test_analyze_returns_delegates_to_service(
        mock_return_analyzer_service: ReturnAnalyzerService,
        sample_ast: DeclarationAggregate,
    ) -> None:
    '''
    Test that AnalyzeReturns calls return_analyzer_service.analyze and
    returns the produced warnings list.

    :param mock_return_analyzer_service: The mock return analyzer service.
    :type mock_return_analyzer_service: ReturnAnalyzerService
    :param sample_ast: The sample AST root.
    :type sample_ast: DeclarationAggregate
    '''

    # Arrange the service to return a fixed warning list.
    fake_warnings = [{'warning_code': UNREACHABLE_AFTER_RETURN_CODE}]
    mock_return_analyzer_service.analyze.return_value = fake_warnings

    # Execute via DomainEvent.handle.
    result = DomainEvent.handle(
        AnalyzeReturns,
        dependencies={'return_analyzer_service': mock_return_analyzer_service},
        ast=sample_ast,
    )

    # Assert the service was called and the produced warnings are returned.
    assert result is fake_warnings
    mock_return_analyzer_service.analyze.assert_called_once_with(sample_ast)


# ** test: analyze_returns_o0_passthrough
def test_analyze_returns_o0_passthrough(
        mock_return_analyzer_service: ReturnAnalyzerService,
        sample_ast: DeclarationAggregate,
    ) -> None:
    '''
    Test that AnalyzeReturns at O0 returns an empty list without calling
    the service.

    :param mock_return_analyzer_service: The mock return analyzer service.
    :type mock_return_analyzer_service: ReturnAnalyzerService
    :param sample_ast: The sample AST root.
    :type sample_ast: DeclarationAggregate
    '''

    # Execute at O0.
    result = DomainEvent.handle(
        AnalyzeReturns,
        dependencies={'return_analyzer_service': mock_return_analyzer_service},
        ast=sample_ast,
        O='O0',
    )

    # The service must not be called and the result must be an empty list.
    assert result == []
    mock_return_analyzer_service.analyze.assert_not_called()


# ** test: analyze_returns_missing_ast
def test_analyze_returns_missing_ast(
        mock_return_analyzer_service: ReturnAnalyzerService,
    ) -> None:
    '''
    Test that AnalyzeReturns raises TiferetError when ast is not provided.

    :param mock_return_analyzer_service: The mock return analyzer service.
    :type mock_return_analyzer_service: ReturnAnalyzerService
    '''

    with pytest.raises(TiferetError):
        DomainEvent.handle(
            AnalyzeReturns,
            dependencies={'return_analyzer_service': mock_return_analyzer_service},
            # ast intentionally omitted
        )


# ** test: analyze_returns_with_real_analyzer
def test_analyze_returns_with_real_analyzer(sample_ast: DeclarationAggregate) -> None:
    '''
    Integration test: AnalyzeReturns using the real ReturnAnalyzer flags
    a statement that follows a return within the same method scope.

    :param sample_ast: The sample AST root (will have a method body added).
    :type sample_ast: DeclarationAggregate
    '''

    # Build: method body = return; expr (dead code).
    ret = StatementAggregate(
        kind=StatementKind.RETURN,
        expr=ExpressionAggregate(kind=ExprKind.NAME, name='result'),
        lineno=10,
        col=8,
    )
    dead = StatementAggregate(
        kind=StatementKind.EXPR,
        expr=ExpressionAggregate(kind=ExprKind.NAME, name='noop'),
        lineno=11,
        col=8,
    )
    ret.next = dead

    # Wrap the method body in a FUNC declaration, then in a module decl stmt.
    method = DeclarationAggregate(
        name='execute',
        type=TypeAggregate(kind=TypeKind.FUNC),
        code=ret,
    )
    sample_ast.code = StatementAggregate(
        kind=StatementKind.DECL,
        decl=method,
        lineno=1,
    )

    # Execute with the real ReturnAnalyzer.
    result = DomainEvent.handle(
        AnalyzeReturns,
        dependencies={'return_analyzer_service': ReturnAnalyzer()},
        ast=sample_ast,
    )

    # A single warning should be produced for the trailing EXPR statement.
    assert len(result) == 1
    assert result[0]['warning_code'] == UNREACHABLE_AFTER_RETURN_CODE
    assert result[0]['lineno'] == 11
    assert result[0]['return_lineno'] == 10
    assert result[0]['scope_path'] == 'module.execute'


# ** fixture: mock_dead_code_eliminator_service
@pytest.fixture
def mock_dead_code_eliminator_service() -> DeadCodeEliminatorService:
    '''
    Returns a mock DeadCodeEliminatorService for testing.

    :return: A mock DeadCodeEliminatorService.
    :rtype: DeadCodeEliminatorService
    '''

    return mock.Mock(spec=DeadCodeEliminatorService)


# *** tests — EliminateDeadCode

# ** test: eliminate_dead_code_delegates_to_service
def test_eliminate_dead_code_delegates_to_service(
        mock_dead_code_eliminator_service: DeadCodeEliminatorService,
        sample_ast: DeclarationAggregate,
    ) -> None:
    '''
    Test that EliminateDeadCode calls dead_code_eliminator_service.eliminate
    and returns the produced (possibly mutated) AST.

    :param mock_dead_code_eliminator_service: The mock eliminator service.
    :type mock_dead_code_eliminator_service: DeadCodeEliminatorService
    :param sample_ast: The sample AST root.
    :type sample_ast: DeclarationAggregate
    '''

    # Arrange the service to return the same AST root.
    mock_dead_code_eliminator_service.eliminate.return_value = sample_ast

    # Execute via DomainEvent.handle.
    result = DomainEvent.handle(
        EliminateDeadCode,
        dependencies={'dead_code_eliminator_service': mock_dead_code_eliminator_service},
        ast=sample_ast,
    )

    # Assert the service was called and the result is the returned AST.
    assert result is sample_ast
    mock_dead_code_eliminator_service.eliminate.assert_called_once_with(sample_ast)


# ** test: eliminate_dead_code_o0_passthrough
def test_eliminate_dead_code_o0_passthrough(
        mock_dead_code_eliminator_service: DeadCodeEliminatorService,
        sample_ast: DeclarationAggregate,
    ) -> None:
    '''
    Test that EliminateDeadCode at O0 returns the AST unchanged without
    calling the service.

    :param mock_dead_code_eliminator_service: The mock eliminator service.
    :type mock_dead_code_eliminator_service: DeadCodeEliminatorService
    :param sample_ast: The sample AST root.
    :type sample_ast: DeclarationAggregate
    '''

    # Execute at O0.
    result = DomainEvent.handle(
        EliminateDeadCode,
        dependencies={'dead_code_eliminator_service': mock_dead_code_eliminator_service},
        ast=sample_ast,
        O='O0',
    )

    # The original AST must be returned and the service must not be called.
    assert result is sample_ast
    mock_dead_code_eliminator_service.eliminate.assert_not_called()


# ** test: eliminate_dead_code_missing_ast
def test_eliminate_dead_code_missing_ast(
        mock_dead_code_eliminator_service: DeadCodeEliminatorService,
    ) -> None:
    '''
    Test that EliminateDeadCode raises TiferetError when ast is not provided.

    :param mock_dead_code_eliminator_service: The mock eliminator service.
    :type mock_dead_code_eliminator_service: DeadCodeEliminatorService
    '''

    with pytest.raises(TiferetError):
        DomainEvent.handle(
            EliminateDeadCode,
            dependencies={'dead_code_eliminator_service': mock_dead_code_eliminator_service},
            # ast intentionally omitted
        )


# ** test: eliminate_dead_code_with_real_eliminator
def test_eliminate_dead_code_with_real_eliminator(sample_ast: DeclarationAggregate) -> None:
    '''
    Integration test: EliminateDeadCode using the real DeadCodeEliminator
    detaches a statement that follows a return inside a method body.

    :param sample_ast: The sample AST root (will have a method body added).
    :type sample_ast: DeclarationAggregate
    '''

    # Build: method body = return; expr (dead code).
    ret = StatementAggregate(
        kind=StatementKind.RETURN,
        expr=ExpressionAggregate(kind=ExprKind.NAME, name='result'),
        lineno=10,
        col=8,
    )
    dead = StatementAggregate(
        kind=StatementKind.EXPR,
        expr=ExpressionAggregate(kind=ExprKind.NAME, name='noop'),
        lineno=11,
        col=8,
    )
    ret.next = dead

    # Wrap the method body in a FUNC declaration, then in a module decl stmt.
    method = DeclarationAggregate(
        name='execute',
        type=TypeAggregate(kind=TypeKind.FUNC),
        code=ret,
    )
    sample_ast.code = StatementAggregate(
        kind=StatementKind.DECL,
        decl=method,
        lineno=1,
    )

    # Execute with the real DeadCodeEliminator.
    result = DomainEvent.handle(
        EliminateDeadCode,
        dependencies={'dead_code_eliminator_service': DeadCodeEliminator()},
        ast=sample_ast,
    )

    # The method body must now end at the return; the trailing EXPR is gone.
    body = result.code.decl.code
    assert body is ret
    assert body.next is None
