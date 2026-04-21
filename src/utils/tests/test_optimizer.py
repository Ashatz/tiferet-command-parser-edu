"""Utils – YamlAnchorOptimizer, ConstantFolder, and StrengthReducer Tests"""

# *** imports

# ** infra
import pytest

# ** app
from ...domain.ast import ExprKind, StatementKind, TypeKind
from ...mappers.ast import (
    ExpressionAggregate,
    StatementAggregate,
    DeclarationAggregate,
    TypeAggregate,
)
from ..optimizer import (
    YamlAnchorOptimizer,
    ConstantFolder,
    StrengthReducer,
    ReturnAnalyzer,
    UNREACHABLE_AFTER_RETURN_CODE,
)

# *** fixtures

# ** fixture: optimizer
@pytest.fixture
def optimizer() -> YamlAnchorOptimizer:
    '''
    Returns a fresh YamlAnchorOptimizer instance.

    :return: A YamlAnchorOptimizer.
    :rtype: YamlAnchorOptimizer
    '''

    return YamlAnchorOptimizer()


# ** fixture: no_events_codegen
@pytest.fixture
def no_events_codegen() -> dict:
    '''
    Returns a codegen dict with imports but no events.

    :return: A codegen dict without events.
    :rtype: dict
    '''

    return {
        'evt_grp': {
            'name': 'imports_only',
            'impt': {
                'app': [{'src': '.settings', 'tgts': ['DomainEvent']}],
            },
        }
    }


# ** fixture: single_event_codegen
@pytest.fixture
def single_event_codegen() -> dict:
    '''
    Returns a codegen dict with a single event.

    :return: A codegen dict with one event.
    :rtype: dict
    '''

    return {
        'evt_grp': {
            'name': 'single',
            'evts': {
                'ping': {
                    'name': 'Ping',
                    'execute': {
                        'params': ['kwargs:dict:false::'],
                        'returns': ['str:'],
                    },
                },
            },
        }
    }


# ** fixture: multiple_events_codegen
@pytest.fixture
def multiple_events_codegen() -> dict:
    '''
    Returns a codegen dict with multiple events sharing identical params/returns.

    :return: A codegen dict with repeated structures.
    :rtype: dict
    '''

    return {
        'evt_grp': {
            'name': 'operators',
            'evts': {
                'add': {
                    'name': 'Add',
                    'execute': {
                        'params': ['a:int:true::', 'b:int:true::'],
                        'returns': ['int:'],
                    },
                },
                'subtract': {
                    'name': 'Subtract',
                    'execute': {
                        'params': ['a:int:true::', 'b:int:true::'],
                        'returns': ['int:'],
                    },
                },
                'divide': {
                    'name': 'Divide',
                    'execute': {
                        'params': ['a:int:true::', 'b:int:true::'],
                        'returns': ['float:'],
                    },
                },
            },
        }
    }


# *** tests

# ** test: no_events_passthrough
def test_no_events_passthrough(optimizer: YamlAnchorOptimizer, no_events_codegen: dict) -> None:
    '''
    Test that a dict with no events returns unchanged with empty registry.

    :param optimizer: The optimizer instance.
    :type optimizer: YamlAnchorOptimizer
    :param no_events_codegen: A codegen dict without events.
    :type no_events_codegen: dict
    '''

    # Optimize the dict.
    result = optimizer.optimize(no_events_codegen)

    # Assert unchanged.
    assert result is no_events_codegen


# ** test: single_event_no_anchors
def test_single_event_no_anchors(optimizer: YamlAnchorOptimizer, single_event_codegen: dict) -> None:
    '''
    Test that a single event has nothing to deduplicate.

    :param optimizer: The optimizer instance.
    :type optimizer: YamlAnchorOptimizer
    :param single_event_codegen: A codegen dict with one event.
    :type single_event_codegen: dict
    '''

    # Optimize the dict.
    result = optimizer.optimize(single_event_codegen)

    # Assert no shared references created for single occurrences.
    assert result is single_event_codegen


# ** test: multiple_events_params_anchored
def test_multiple_events_params_anchored(optimizer: YamlAnchorOptimizer, multiple_events_codegen: dict) -> None:
    '''
    Test that identical params lists across events produce shared objects.

    :param optimizer: The optimizer instance.
    :type optimizer: YamlAnchorOptimizer
    :param multiple_events_codegen: A codegen dict with repeated params.
    :type multiple_events_codegen: dict
    '''

    # Optimize the dict.
    result = optimizer.optimize(multiple_events_codegen)
    evts = result['evt_grp']['evts']

    # All three events should share the same params list object.
    assert evts['add']['execute']['params'] is evts['subtract']['execute']['params']
    assert evts['add']['execute']['params'] is evts['divide']['execute']['params']

    # The shared object should also appear in vars.
    assert 'vars' in result
    assert evts['add']['execute']['params'] in result['vars']


# ** test: multiple_events_returns_anchored
def test_multiple_events_returns_anchored(optimizer: YamlAnchorOptimizer, multiple_events_codegen: dict) -> None:
    '''
    Test that identical returns lists produce shared objects.

    :param optimizer: The optimizer instance.
    :type optimizer: YamlAnchorOptimizer
    :param multiple_events_codegen: A codegen dict with repeated returns.
    :type multiple_events_codegen: dict
    '''

    # Optimize the dict.
    result = optimizer.optimize(multiple_events_codegen)
    evts = result['evt_grp']['evts']

    # Add and subtract share the same int returns.
    assert evts['add']['execute']['returns'] is evts['subtract']['execute']['returns']

    # Divide has a different returns (float) so it stays independent.
    assert evts['add']['execute']['returns'] is not evts['divide']['execute']['returns']

    # The shared int returns should appear in vars.
    assert evts['add']['execute']['returns'] in result['vars']


# ** test: vars_not_present_without_duplicates
def test_vars_not_present_without_duplicates(optimizer: YamlAnchorOptimizer, single_event_codegen: dict) -> None:
    '''
    Test that the vars key is not added when there are no repeated structures.

    :param optimizer: The optimizer instance.
    :type optimizer: YamlAnchorOptimizer
    :param single_event_codegen: A codegen dict with one event.
    :type single_event_codegen: dict
    '''

    # Optimize the dict.
    result = optimizer.optimize(single_event_codegen)

    # No vars section should be present.
    assert 'vars' not in result


# *** fixtures — ConstantFolder

# ** fixture: folder
@pytest.fixture
def folder() -> ConstantFolder:
    '''
    Returns a fresh ConstantFolder instance.

    :return: A ConstantFolder.
    :rtype: ConstantFolder
    '''

    return ConstantFolder()


# ** fixture: int_lit
def int_lit(value: str, lineno: int = 1, col: int = 0) -> ExpressionAggregate:
    '''
    Helper: create an INT_VAL literal expression.

    :param value: The integer string value.
    :type value: str
    :return: An ExpressionAggregate of kind INT_VAL.
    :rtype: ExpressionAggregate
    '''

    return ExpressionAggregate(kind=ExprKind.INT_VAL, value=value, lineno=lineno, col=col)


# ** fixture: num_lit
def num_lit(value: str) -> ExpressionAggregate:
    '''
    Helper: create a NUM_VAL literal expression.

    :param value: The float string value.
    :type value: str
    :return: An ExpressionAggregate of kind NUM_VAL.
    :rtype: ExpressionAggregate
    '''

    return ExpressionAggregate(kind=ExprKind.NUM_VAL, value=value)


# ** fixture: name_expr
def name_expr(name: str) -> ExpressionAggregate:
    '''
    Helper: create a NAME expression (variable reference).

    :param name: The variable name.
    :type name: str
    :return: An ExpressionAggregate of kind NAME.
    :rtype: ExpressionAggregate
    '''

    return ExpressionAggregate(kind=ExprKind.NAME, name=name)


# *** tests — ConstantFolder

# ** test: fold_simple_integer_add
def test_fold_simple_integer_add(folder: ConstantFolder) -> None:
    '''
    Test that two INT_VAL operands connected by ADD are folded to a single INT_VAL.

    :param folder: The ConstantFolder instance.
    :type folder: ConstantFolder
    '''

    # Build: 3 + 5
    expr = ExpressionAggregate(
        kind=ExprKind.ADD,
        left=int_lit('3'),
        right=int_lit('5'),
        lineno=1,
        col=0,
    )

    # Fold the expression.
    result = folder.fold_expression(expr)

    # Assert the result is a single INT_VAL with value 8.
    assert result.kind == ExprKind.INT_VAL
    assert result.value == '8'


# ** test: fold_integer_multiply
def test_fold_integer_multiply(folder: ConstantFolder) -> None:
    '''
    Test that 3 * 5 is folded to INT_VAL 15.

    :param folder: The ConstantFolder instance.
    :type folder: ConstantFolder
    '''

    # Build: 3 * 5
    expr = ExpressionAggregate(
        kind=ExprKind.MUL,
        left=int_lit('3'),
        right=int_lit('5'),
    )

    # Fold the expression.
    result = folder.fold_expression(expr)

    # Assert the result is INT_VAL 15.
    assert result.kind == ExprKind.INT_VAL
    assert result.value == '15'


# ** test: fold_division_yields_num_val
def test_fold_division_yields_num_val(folder: ConstantFolder) -> None:
    '''
    Test that division always produces a NUM_VAL, even for whole-number results.

    :param folder: The ConstantFolder instance.
    :type folder: ConstantFolder
    '''

    # Build: 10 / 4
    expr = ExpressionAggregate(
        kind=ExprKind.DIV,
        left=int_lit('10'),
        right=int_lit('4'),
    )

    # Fold the expression.
    result = folder.fold_expression(expr)

    # Division always yields NUM_VAL.
    assert result.kind == ExprKind.NUM_VAL
    assert result.value == '2.5'


# ** test: fold_nested_constants
def test_fold_nested_constants(folder: ConstantFolder) -> None:
    '''
    Test that nested constant sub-expressions fold bottom-up.
    (3 * 5) * 2 should collapse first to 15 * 2, then to 30.

    :param folder: The ConstantFolder instance.
    :type folder: ConstantFolder
    '''

    # Build: (3 * 5) * 2
    inner = ExpressionAggregate(kind=ExprKind.MUL, left=int_lit('3'), right=int_lit('5'))
    outer = ExpressionAggregate(kind=ExprKind.MUL, left=inner, right=int_lit('2'))

    # Fold the expression.
    result = folder.fold_expression(outer)

    # Both levels collapsed to a single INT_VAL 30.
    assert result.kind == ExprKind.INT_VAL
    assert result.value == '30'


# ** test: fold_str_val_numerics
def test_fold_str_val_numerics(folder: ConstantFolder) -> None:
    '''
    Test that STR_VAL nodes whose content is a numeric string are foldable.
    This matches the parser\'s convention of storing token values as STR_VAL.

    :param folder: The ConstantFolder instance.
    :type folder: ConstantFolder
    '''

    # Build: STR_VAL('3') * STR_VAL('5')  — the common parser output for 3 * 5
    lhs = ExpressionAggregate(kind=ExprKind.STR_VAL, value='3')
    rhs = ExpressionAggregate(kind=ExprKind.STR_VAL, value='5')
    expr = ExpressionAggregate(kind=ExprKind.MUL, left=lhs, right=rhs)

    # Fold the expression.
    result = folder.fold_expression(expr)

    # The result should be a STR_VAL with value 15.
    assert result.kind == ExprKind.STR_VAL
    assert result.value == '15'


# ** test: fold_preserves_variable_operand
def test_fold_preserves_variable_operand(folder: ConstantFolder) -> None:
    '''
    Test that a constant sub-expression is folded while its variable sibling
    is preserved, matching the sample pattern: x + (4 * 5) -> x + 20.

    :param folder: The ConstantFolder instance.
    :type folder: ConstantFolder
    '''

    # Build: x + (4 * 5)  using STR_VAL operands as the parser would produce
    const_sub = ExpressionAggregate(
        kind=ExprKind.MUL,
        left=ExpressionAggregate(kind=ExprKind.STR_VAL, value='4'),
        right=ExpressionAggregate(kind=ExprKind.STR_VAL, value='5'),
    )
    expr = ExpressionAggregate(kind=ExprKind.ADD, left=name_expr('x'), right=const_sub)

    # Fold the expression.
    result = folder.fold_expression(expr)

    # Outer ADD is preserved; right child has been folded to STR_VAL 20
    # (STR_VAL operands produce STR_VAL results, matching parser convention).
    assert result.kind == ExprKind.ADD
    assert result.left.kind == ExprKind.NAME
    assert result.right.kind == ExprKind.STR_VAL
    assert result.right.value == '20'


# ** test: fold_preserves_name_expression
def test_fold_preserves_name_expression(folder: ConstantFolder) -> None:
    '''
    Test that a plain NAME expression is returned unchanged.

    :param folder: The ConstantFolder instance.
    :type folder: ConstantFolder
    '''

    # Build: a plain name expression.
    expr = name_expr('penalty')

    # Fold the expression.
    result = folder.fold_expression(expr)

    # The expression is unchanged.
    assert result is expr
    assert result.kind == ExprKind.NAME


# ** test: fold_ast_return_statement
def test_fold_ast_return_statement(folder: ConstantFolder) -> None:
    '''
    Test that fold() traverses a return statement inside a module declaration
    and folds the constant return expression.

    :param folder: The ConstantFolder instance.
    :type folder: ConstantFolder
    '''

    # Build return statement: return 4 * 5
    const_expr = ExpressionAggregate(kind=ExprKind.MUL, left=int_lit('4'), right=int_lit('5'))
    return_stmt = StatementAggregate(kind=StatementKind.RETURN, expr=const_expr)

    # Wrap in a minimal module declaration.
    module_decl = DeclarationAggregate(name='test_module', code=return_stmt)

    # Apply the full fold pass.
    result = folder.fold(module_decl)

    # The return expression should now be INT_VAL 20.
    folded_expr = result.code.expr
    assert folded_expr.kind == ExprKind.INT_VAL
    assert folded_expr.value == '20'


# ** fixture: reducer
@pytest.fixture
def reducer() -> StrengthReducer:
    '''
    Returns a fresh StrengthReducer instance.

    :return: A StrengthReducer.
    :rtype: StrengthReducer
    '''

    return StrengthReducer()


# ** test: is_power_of_two_literal_positive
def test_is_power_of_two_literal_positive(reducer: StrengthReducer) -> None:
    '''
    Test that positive integer power-of-two literals produce their exponent.

    :param reducer: The StrengthReducer instance.
    :type reducer: StrengthReducer
    '''

    # 1 (2**0), 2 (2**1), 4 (2**2), 8 (2**3), 1024 (2**10).
    assert reducer.is_power_of_two_literal(int_lit('1')) == 0
    assert reducer.is_power_of_two_literal(int_lit('2')) == 1
    assert reducer.is_power_of_two_literal(int_lit('4')) == 2
    assert reducer.is_power_of_two_literal(int_lit('8')) == 3
    assert reducer.is_power_of_two_literal(int_lit('1024')) == 10


# ** test: is_power_of_two_literal_negative
def test_is_power_of_two_literal_negative(reducer: StrengthReducer) -> None:
    '''
    Test that non-power-of-two, zero, negative, non-integer, and non-literal
    inputs all return None.

    :param reducer: The StrengthReducer instance.
    :type reducer: StrengthReducer
    '''

    # Non-power-of-two integers.
    assert reducer.is_power_of_two_literal(int_lit('3')) is None
    assert reducer.is_power_of_two_literal(int_lit('6')) is None
    assert reducer.is_power_of_two_literal(int_lit('1000')) is None

    # Zero and negative.
    assert reducer.is_power_of_two_literal(int_lit('0')) is None
    assert reducer.is_power_of_two_literal(int_lit('-2')) is None

    # Fractional float.
    assert reducer.is_power_of_two_literal(num_lit('2.5')) is None

    # Variable reference.
    assert reducer.is_power_of_two_literal(name_expr('x')) is None

    # None / empty value.
    assert reducer.is_power_of_two_literal(None) is None


# ** test: reduce_mul_right_literal
def test_reduce_mul_right_literal(reducer: StrengthReducer) -> None:
    '''
    Test that x * 8 is reduced to x << 3.

    :param reducer: The StrengthReducer instance.
    :type reducer: StrengthReducer
    '''

    # Build: x * 8.
    expr = ExpressionAggregate(
        kind=ExprKind.MUL,
        left=name_expr('x'),
        right=int_lit('8'),
        lineno=2,
        col=4,
    )

    # Reduce.
    result = reducer.reduce_expression(expr)

    # Assert shape: x << 3.
    assert result.kind == ExprKind.SHL
    assert result.value == '<<'
    assert result.left.kind == ExprKind.NAME
    assert result.left.name == 'x'
    assert result.right.kind == ExprKind.INT_VAL
    assert result.right.value == '3'
    # Outer position preserved from the original MUL.
    assert result.lineno == 2
    assert result.col == 4


# ** test: reduce_mul_left_literal
def test_reduce_mul_left_literal(reducer: StrengthReducer) -> None:
    '''
    Test that 4 * y is reduced to y << 2 (multiplication is commutative).

    :param reducer: The StrengthReducer instance.
    :type reducer: StrengthReducer
    '''

    # Build: 4 * y.
    expr = ExpressionAggregate(
        kind=ExprKind.MUL,
        left=int_lit('4'),
        right=name_expr('y'),
    )

    # Reduce.
    result = reducer.reduce_expression(expr)

    # Assert shape: y << 2.
    assert result.kind == ExprKind.SHL
    assert result.left.kind == ExprKind.NAME
    assert result.left.name == 'y'
    assert result.right.kind == ExprKind.INT_VAL
    assert result.right.value == '2'


# ** test: reduce_div_power_of_two
def test_reduce_div_power_of_two(reducer: StrengthReducer) -> None:
    '''
    Test that x / 4 is reduced to x >> 2.

    :param reducer: The StrengthReducer instance.
    :type reducer: StrengthReducer
    '''

    # Build: x / 4.
    expr = ExpressionAggregate(
        kind=ExprKind.DIV,
        left=name_expr('x'),
        right=int_lit('4'),
    )

    # Reduce.
    result = reducer.reduce_expression(expr)

    # Assert shape: x >> 2.
    assert result.kind == ExprKind.SHR
    assert result.value == '>>'
    assert result.left.kind == ExprKind.NAME
    assert result.left.name == 'x'
    assert result.right.kind == ExprKind.INT_VAL
    assert result.right.value == '2'


# ** test: reduce_div_numerator_literal_untouched
def test_reduce_div_numerator_literal_untouched(reducer: StrengthReducer) -> None:
    '''
    Test that 8 / x is NOT rewritten (division is not commutative).

    :param reducer: The StrengthReducer instance.
    :type reducer: StrengthReducer
    '''

    # Build: 8 / x.
    expr = ExpressionAggregate(
        kind=ExprKind.DIV,
        left=int_lit('8'),
        right=name_expr('x'),
    )

    # Reduce.
    result = reducer.reduce_expression(expr)

    # The DIV node must remain intact.
    assert result is expr
    assert result.kind == ExprKind.DIV


# ** test: reduce_exp_by_two
def test_reduce_exp_by_two(reducer: StrengthReducer) -> None:
    '''
    Test that x ** 2 is reduced to x * x with two distinct operand nodes.

    :param reducer: The StrengthReducer instance.
    :type reducer: StrengthReducer
    '''

    # Build: x ** 2.
    expr = ExpressionAggregate(
        kind=ExprKind.EXP,
        left=name_expr('x'),
        right=int_lit('2'),
    )

    # Reduce.
    result = reducer.reduce_expression(expr)

    # Assert shape: x * x.
    assert result.kind == ExprKind.MUL
    assert result.value == '*'
    assert result.left.kind == ExprKind.NAME
    assert result.right.kind == ExprKind.NAME
    assert result.left.name == 'x'
    assert result.right.name == 'x'
    # The two children must be distinct objects.
    assert result.left is not result.right


# ** test: reduce_exp_by_three_untouched
def test_reduce_exp_by_three_untouched(reducer: StrengthReducer) -> None:
    '''
    Test that x ** 3 is left alone (only the exact literal 2 triggers the rewrite).

    :param reducer: The StrengthReducer instance.
    :type reducer: StrengthReducer
    '''

    # Build: x ** 3.
    expr = ExpressionAggregate(
        kind=ExprKind.EXP,
        left=name_expr('x'),
        right=int_lit('3'),
    )

    # Reduce.
    result = reducer.reduce_expression(expr)

    # The EXP node must remain intact.
    assert result is expr
    assert result.kind == ExprKind.EXP


# ** test: reduce_non_power_of_two_untouched
def test_reduce_non_power_of_two_untouched(reducer: StrengthReducer) -> None:
    '''
    Test that x * 3 is NOT rewritten because 3 is not a power of two.

    :param reducer: The StrengthReducer instance.
    :type reducer: StrengthReducer
    '''

    # Build: x * 3.
    expr = ExpressionAggregate(
        kind=ExprKind.MUL,
        left=name_expr('x'),
        right=int_lit('3'),
    )

    # Reduce.
    result = reducer.reduce_expression(expr)

    # The MUL node must remain intact.
    assert result is expr
    assert result.kind == ExprKind.MUL


# ** test: reduce_mul_by_one_untouched
def test_reduce_mul_by_one_untouched(reducer: StrengthReducer) -> None:
    '''
    Test that x * 1 is NOT rewritten (2**0 shift is a no-op; leave the
    original MUL in place so other passes can handle identity folding).

    :param reducer: The StrengthReducer instance.
    :type reducer: StrengthReducer
    '''

    # Build: x * 1.
    expr = ExpressionAggregate(
        kind=ExprKind.MUL,
        left=name_expr('x'),
        right=int_lit('1'),
    )

    # Reduce.
    result = reducer.reduce_expression(expr)

    # The MUL node must remain intact (k < 1 not rewritten).
    assert result is expr
    assert result.kind == ExprKind.MUL


# ** test: reduce_plain_name_untouched
def test_reduce_plain_name_untouched(reducer: StrengthReducer) -> None:
    '''
    Test that a plain NAME expression is returned unchanged.

    :param reducer: The StrengthReducer instance.
    :type reducer: StrengthReducer
    '''

    # Build: plain name.
    expr = name_expr('penalty')

    # Reduce.
    result = reducer.reduce_expression(expr)

    # Returned unchanged.
    assert result is expr
    assert result.kind == ExprKind.NAME


# ** test: reduce_nested_inside_add
def test_reduce_nested_inside_add(reducer: StrengthReducer) -> None:
    '''
    Test that nested strength-reducible sub-expressions are rewritten while
    the outer ADD is preserved. (a * 8) + (b / 4) -> (a << 3) + (b >> 2).

    :param reducer: The StrengthReducer instance.
    :type reducer: StrengthReducer
    '''

    # Build: (a * 8) + (b / 4).
    left = ExpressionAggregate(kind=ExprKind.MUL, left=name_expr('a'), right=int_lit('8'))
    right = ExpressionAggregate(kind=ExprKind.DIV, left=name_expr('b'), right=int_lit('4'))
    expr = ExpressionAggregate(kind=ExprKind.ADD, left=left, right=right)

    # Reduce.
    result = reducer.reduce_expression(expr)

    # Outer ADD preserved; children rewritten.
    assert result.kind == ExprKind.ADD
    assert result.left.kind == ExprKind.SHL
    assert result.left.right.value == '3'
    assert result.right.kind == ExprKind.SHR
    assert result.right.right.value == '2'


# ** test: reduce_fold_combined
def test_reduce_fold_combined(reducer: StrengthReducer, folder: ConstantFolder) -> None:
    '''
    Test the constant-folder + strength-reducer pipeline: (2 * 4) * x
    first folds to 8 * x, then reduces to x << 3.

    :param reducer: The StrengthReducer instance.
    :type reducer: StrengthReducer
    :param folder: The ConstantFolder instance.
    :type folder: ConstantFolder
    '''

    # Build: (2 * 4) * x.
    inner = ExpressionAggregate(kind=ExprKind.MUL, left=int_lit('2'), right=int_lit('4'))
    expr = ExpressionAggregate(kind=ExprKind.MUL, left=inner, right=name_expr('x'))

    # Fold first, then reduce.
    folded = folder.fold_expression(expr)
    result = reducer.reduce_expression(folded)

    # Final shape: x << 3.
    assert result.kind == ExprKind.SHL
    assert result.left.kind == ExprKind.NAME
    assert result.left.name == 'x'
    assert result.right.kind == ExprKind.INT_VAL
    assert result.right.value == '3'


# ** test: reduce_ast_return_statement
def test_reduce_ast_return_statement(reducer: StrengthReducer) -> None:
    '''
    Test that reduce() traverses a return statement inside a module
    declaration and rewrites the inner MUL into a SHL.

    :param reducer: The StrengthReducer instance.
    :type reducer: StrengthReducer
    '''

    # Build return statement: return x * 8.
    mul_expr = ExpressionAggregate(
        kind=ExprKind.MUL,
        left=name_expr('x'),
        right=int_lit('8'),
    )
    return_stmt = StatementAggregate(kind=StatementKind.RETURN, expr=mul_expr)

    # Wrap in a minimal module declaration.
    module_decl = DeclarationAggregate(name='test_module', code=return_stmt)

    # Apply the full reduce pass.
    result = reducer.reduce(module_decl)

    # The return expression should now be a SHL.
    reduced_expr = result.code.expr
    assert reduced_expr.kind == ExprKind.SHL
    assert reduced_expr.left.name == 'x'
    assert reduced_expr.right.value == '3'


# ** fixture: analyzer
@pytest.fixture
def analyzer() -> ReturnAnalyzer:
    '''
    Returns a fresh ReturnAnalyzer instance.

    :return: A ReturnAnalyzer.
    :rtype: ReturnAnalyzer
    '''

    return ReturnAnalyzer()


# ** fixture: make_expr_stmt
def make_expr_stmt(lineno: int, col: int = 4) -> StatementAggregate:
    '''
    Helper: build an EXPR statement with a trivial name expression.

    :param lineno: Source line number to attach.
    :type lineno: int
    :param col: Source column to attach.
    :type col: int
    :return: An EXPR statement aggregate.
    :rtype: StatementAggregate
    '''

    return StatementAggregate(
        kind=StatementKind.EXPR,
        expr=ExpressionAggregate(kind=ExprKind.NAME, name='noop'),
        lineno=lineno,
        col=col,
    )


# ** fixture: make_return_stmt
def make_return_stmt(lineno: int, col: int = 4) -> StatementAggregate:
    '''
    Helper: build a RETURN statement with a trivial name expression.

    :param lineno: Source line number to attach.
    :type lineno: int
    :param col: Source column to attach.
    :type col: int
    :return: A RETURN statement aggregate.
    :rtype: StatementAggregate
    '''

    return StatementAggregate(
        kind=StatementKind.RETURN,
        expr=ExpressionAggregate(kind=ExprKind.NAME, name='result'),
        lineno=lineno,
        col=col,
    )


# ** fixture: make_if_else_stmt
def make_if_else_stmt(
        lineno: int,
        body: StatementAggregate,
        else_body: StatementAggregate,
        col: int = 4,
    ) -> StatementAggregate:
    '''
    Helper: build an IF_ELSE statement with explicit body and else_body chains.
    Used to exercise ReturnAnalyzer.block_always_returns at the AST level,
    independent of the current parser INDENT/DEDENT limitations.

    :param lineno: Source line number.
    :type lineno: int
    :param body: The if-branch statement chain.
    :type body: StatementAggregate
    :param else_body: The else-branch statement chain.
    :type else_body: StatementAggregate
    :param col: Source column.
    :type col: int
    :return: An IF_ELSE statement aggregate.
    :rtype: StatementAggregate
    '''

    return StatementAggregate(
        kind=StatementKind.IF_ELSE,
        expr=ExpressionAggregate(kind=ExprKind.NAME, name='cond'),
        body=body,
        else_body=else_body,
        lineno=lineno,
        col=col,
    )


# ** fixture: method_decl
def method_decl(name: str, body: StatementAggregate) -> DeclarationAggregate:
    '''
    Helper: wrap a statement chain in a FUNC-typed declaration so the
    analyzer pushes a named scope while walking it.

    :param name: The method name used as the scope segment.
    :type name: str
    :param body: The method body statement chain.
    :type body: StatementAggregate
    :return: A FUNC DeclarationAggregate.
    :rtype: DeclarationAggregate
    '''

    return DeclarationAggregate(
        name=name,
        type=TypeAggregate(kind=TypeKind.FUNC),
        code=body,
    )


# ** test: analyze_no_returns_empty
def test_analyze_no_returns_empty(analyzer: ReturnAnalyzer) -> None:
    '''
    Test that a statement chain with no returns yields no warnings.

    :param analyzer: The ReturnAnalyzer instance.
    :type analyzer: ReturnAnalyzer
    '''

    # Build a body of two EXPR statements chained with no return.
    first = make_expr_stmt(lineno=1)
    first.next = make_expr_stmt(lineno=2)
    decl = method_decl('plain', first)

    # Wrap in a minimal module and analyze.
    module = DeclarationAggregate(name='test_module', code=StatementAggregate(
        kind=StatementKind.DECL,
        decl=decl,
        lineno=1,
    ))

    # No returns present -> no warnings.
    warnings = analyzer.analyze(module)
    assert warnings == []


# ** test: analyze_return_at_end_clean
def test_analyze_return_at_end_clean(analyzer: ReturnAnalyzer) -> None:
    '''
    Test that a trailing return with nothing after it produces no warnings.

    :param analyzer: The ReturnAnalyzer instance.
    :type analyzer: ReturnAnalyzer
    '''

    # Build: expr; return.
    first = make_expr_stmt(lineno=1)
    first.next = make_return_stmt(lineno=2)
    decl = method_decl('clean', first)

    # Wrap in a module declaration and analyze.
    module = DeclarationAggregate(name='test_module', code=StatementAggregate(
        kind=StatementKind.DECL,
        decl=decl,
        lineno=1,
    ))

    # The return is the last stmt -> nothing to flag.
    warnings = analyzer.analyze(module)
    assert warnings == []


# ** test: analyze_statements_after_return_flagged
def test_analyze_statements_after_return_flagged(analyzer: ReturnAnalyzer) -> None:
    '''
    Test that two statements following a return are both flagged with
    positions and the scope_path reflects the enclosing function.

    :param analyzer: The ReturnAnalyzer instance.
    :type analyzer: ReturnAnalyzer
    '''

    # Build: return; expr; expr.
    ret = make_return_stmt(lineno=10, col=8)
    dead_a = make_expr_stmt(lineno=11, col=8)
    dead_b = make_expr_stmt(lineno=12, col=8)
    ret.next = dead_a
    dead_a.next = dead_b
    decl = method_decl('describe', ret)

    # Wrap in a module declaration and analyze.
    module = DeclarationAggregate(name='test_module', code=StatementAggregate(
        kind=StatementKind.DECL,
        decl=decl,
        lineno=1,
    ))

    # Both trailing statements should be flagged against the return.
    warnings = analyzer.analyze(module)
    assert len(warnings) == 2
    assert warnings[0]['warning_code'] == UNREACHABLE_AFTER_RETURN_CODE
    assert warnings[0]['lineno'] == 11
    assert warnings[0]['return_lineno'] == 10
    assert warnings[0]['scope_path'] == 'module.describe'
    assert warnings[1]['lineno'] == 12
    assert warnings[1]['return_lineno'] == 10


# ** test: analyze_nested_scope_boundary
def test_analyze_nested_scope_boundary(analyzer: ReturnAnalyzer) -> None:
    '''
    Test that a return in one method does not flag statements that live
    in a sibling method's body -- scope boundaries isolate terminators.

    :param analyzer: The ReturnAnalyzer instance.
    :type analyzer: ReturnAnalyzer
    '''

    # First method: return followed by a dead statement.
    first_ret = make_return_stmt(lineno=5)
    first_dead = make_expr_stmt(lineno=6)
    first_ret.next = first_dead
    first_decl = method_decl('first', first_ret)

    # Second method: a lone expression with no return. Must not be flagged.
    second_body = make_expr_stmt(lineno=20)
    second_decl = method_decl('second', second_body)

    # Chain the two declarations as siblings in a module body.
    first_stmt = StatementAggregate(
        kind=StatementKind.DECL,
        decl=first_decl,
        lineno=1,
    )
    second_stmt = StatementAggregate(
        kind=StatementKind.DECL,
        decl=second_decl,
        lineno=15,
    )
    first_stmt.next = second_stmt
    module = DeclarationAggregate(name='test_module', code=first_stmt)

    # Only the dead statement in the first method should be flagged.
    warnings = analyzer.analyze(module)
    assert len(warnings) == 1
    assert warnings[0]['lineno'] == 6
    assert warnings[0]['scope_path'] == 'module.first'


# ** test: analyze_if_else_both_branches_return
def test_analyze_if_else_both_branches_return(analyzer: ReturnAnalyzer) -> None:
    '''
    Test the block_always_returns branch logic: an if/else whose body
    and else_body both end in a return acts as a terminator for its
    enclosing chain, so a sibling statement after it is flagged. The
    AST is constructed directly -- this path does not go through the
    parser, so it is unaffected by the current INDENT/DEDENT constraints.

    :param analyzer: The ReturnAnalyzer instance.
    :type analyzer: ReturnAnalyzer
    '''

    # Build body branch: return.
    body = make_return_stmt(lineno=6)

    # Build else branch: return.
    else_body = make_return_stmt(lineno=8)

    # Build: if/else (both branches return); expr (should be flagged).
    if_else = make_if_else_stmt(lineno=5, body=body, else_body=else_body)
    sibling = make_expr_stmt(lineno=10)
    if_else.next = sibling
    decl = method_decl('branching', if_else)

    # Wrap in a module declaration and analyze.
    module = DeclarationAggregate(name='test_module', code=StatementAggregate(
        kind=StatementKind.DECL,
        decl=decl,
        lineno=1,
    ))

    # The trailing sibling is unreachable because every branch returns.
    warnings = analyzer.analyze(module)
    assert len(warnings) == 1
    assert warnings[0]['lineno'] == 10
    assert warnings[0]['return_lineno'] == 5


# ** test: analyze_if_only_one_branch_returns
def test_analyze_if_only_one_branch_returns(analyzer: ReturnAnalyzer) -> None:
    '''
    Test that when only one branch of an if/else ends in a return,
    the enclosing chain is NOT considered terminated and subsequent
    siblings are not flagged.

    :param analyzer: The ReturnAnalyzer instance.
    :type analyzer: ReturnAnalyzer
    '''

    # Build body branch: return.
    body = make_return_stmt(lineno=6)

    # Build else branch: non-return EXPR.
    else_body = make_expr_stmt(lineno=8)

    # Build: if/else (only one branch returns); expr (should NOT be flagged).
    if_else = make_if_else_stmt(lineno=5, body=body, else_body=else_body)
    sibling = make_expr_stmt(lineno=10)
    if_else.next = sibling
    decl = method_decl('partial', if_else)

    # Wrap in a module declaration and analyze.
    module = DeclarationAggregate(name='test_module', code=StatementAggregate(
        kind=StatementKind.DECL,
        decl=decl,
        lineno=1,
    ))

    # No terminator reached at the enclosing chain level.
    warnings = analyzer.analyze(module)
    assert warnings == []
