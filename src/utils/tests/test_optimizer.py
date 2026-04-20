"""Utils – YamlAnchorOptimizer and ConstantFolder Tests"""

# *** imports

# ** infra
import pytest

# ** app
from ...domain.ast import ExprKind, StatementKind
from ...mappers.ast import ExpressionAggregate, StatementAggregate, DeclarationAggregate
from ..optimizer import YamlAnchorOptimizer, ConstantFolder

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
