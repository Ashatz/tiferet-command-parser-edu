"""Domain – AST Domain Objects Tests"""

# *** imports

# ** core
import pytest
from typing import List

# ** app
from ..ast import (
    Type,
    ParamList,
    Expression,
    Declaration,
    Statement,
    TypeKind,
    StatementKind,
    ExprKind,
)

# *** fixtures

# ** fixture: simple_string_type
@pytest.fixture
def simple_string_type() -> Type:
    '''
    Returns a basic string type for reuse in other fixtures and tests.
    
    :return: A Type instance representing the Python 'str' type.
    '''
    
    return Type(
        name='str',
        kind=TypeKind.STR,
        subtype=None,
        params=None
    )

# ** fixture: simple_int_type
@pytest.fixture
def simple_int_type() -> Type:
    '''
    Returns a basic integer type for reuse in other fixtures and tests.
    
    :return: A Type instance representing the Python 'int' type.
    '''
    
    return Type(
        name='int',
        kind=TypeKind.INT,
        subtype=None,
        params=None
    )

# ** fixture: list_of_str_type
@pytest.fixture
def list_of_str_type(simple_string_type: Type) -> Type:
    '''
    Returns a List[str] type using recursive subtype.
    
    :param simple_string_type: The element type (str).
    :return: A Type instance representing list[str].
    '''
    
    return Type(
        name='list',
        kind=TypeKind.LIST,
        subtype=simple_string_type,
        params=None
    )

# ** fixture: single_param
@pytest.fixture
def single_param(simple_string_type: Type) -> ParamList:
    '''
    Returns a single required parameter 'id: str'.
    
    :param simple_string_type: The type of the parameter.
    :return: A ParamList instance for a single parameter.
    '''
    
    return ParamList(
        name='id',
        type=simple_string_type,
        required=True,
        default=None,
        next=None
    )

# ** fixture: two_params
@pytest.fixture
def two_params(single_param: ParamList, simple_string_type: Type) -> ParamList:
    '''
    Returns a chained parameter list: name: str -> id: str.
    
    :param single_param: The next parameter in the chain.
    :param simple_string_type: The type of the current parameter.
    :return: A ParamList instance representing two parameters.
    '''
    
    return ParamList(
        name='name',
        type=simple_string_type,
        required=True,
        default=None,
        next=single_param
    )

# ** fixture: basic_declaration
@pytest.fixture
def basic_declaration(simple_string_type: Type) -> Declaration:
    '''
    Returns a minimal declaration with only required fields.
    
    :param simple_string_type: The type of the declaration.
    :return: A Declaration instance for 'error_service'.
    '''
    
    return Declaration(
        name='error_service',
        type=simple_string_type,
        metadata={},
        doc_string=None,
        value=None,
        code=None,
        next=None
    )

# ** fixture: simple_expression_name
@pytest.fixture
def simple_expression_name() -> Expression:
    '''
    Returns a simple name expression.
    
    :return: An Expression instance with kind=NAME.
    '''
    
    return Expression(
        kind=ExprKind.NAME,
        value=None,
        name='error_service',
        left=None,
        right=None
    )

# ** fixture: simple_expression_int
@pytest.fixture
def simple_expression_int() -> Expression:
    '''
    Returns a simple integer literal expression.
    
    :return: An Expression instance with kind=INT_VAL and value='42'.
    '''
    
    return Expression(
        kind=ExprKind.INT_VAL,
        value='42',
        name=None,
        left=None,
        right=None
    )

# ** fixture: binary_add_expression
@pytest.fixture
def binary_add_expression(simple_expression_int: Expression) -> Expression:
    '''
    Returns a binary add expression (10 + 32).
    
    :param simple_expression_int: The right operand.
    :return: An Expression instance with kind=ADD.
    '''
    
    left = Expression(
        kind=ExprKind.INT_VAL,
        value='10',
        name=None,
        left=None,
        right=None
    )
    return Expression(
        kind=ExprKind.ADD,
        value=None,
        name=None,
        left=left,
        right=simple_expression_int
    )

# ** fixture: simple_statement_expr
@pytest.fixture
def simple_statement_expr(simple_expression_name: Expression) -> Statement:
    '''
    Returns a simple expression statement.
    
    :param simple_expression_name: The inner expression.
    :return: A Statement instance with kind=EXPR.
    '''
    
    return Statement(
        kind=StatementKind.EXPR,
        decl=None,
        init_expr=simple_expression_name,
        expr=None,
        next_expr=None,
        body=None,
        else_body=None,
        next=None
    )

# ** fixture: simple_statement_decl
@pytest.fixture
def simple_statement_decl(basic_declaration: Declaration) -> Statement:
    '''
    Returns a simple declaration statement.
    
    :param basic_declaration: The associated declaration.
    :return: A Statement instance with kind=DECL.
    '''
    
    return Statement(
        kind=StatementKind.DECL,
        decl=basic_declaration,
        inner_expr=None,
        expr=None,
        next_expr=None,
        body=None,
        else_body=None,
        next=None
    )

# *** tests

# ** test: type_creation_and_validation
def test_type_creation_and_validation(simple_string_type: Type, list_of_str_type: Type) -> None:
    '''
    Happy path for simple and recursive Type objects.
    
    :param simple_string_type: Fixture providing a string type.
    :param list_of_str_type: Fixture providing a list[str] type.
    '''
    
    assert simple_string_type.name == 'str'
    assert simple_string_type.kind == TypeKind.STR
    assert simple_string_type.subtype is None
    assert simple_string_type.params is None

    assert list_of_str_type.kind == TypeKind.LIST
    assert list_of_str_type.subtype.name == 'str'

# ** test: type_all_kinds_accepted
def test_type_all_kinds_accepted() -> None:
    '''
    Every kind defined in TypeKind is accepted by the model.
    '''
    
    for kind in TypeKind:
        t = Type(
            name=kind.value,
            kind=kind,
            subtype=None,
            params=None
        )
        # Pydantic v2 auto-validates on creation

# ** test: type_validation_missing_required
def test_type_validation_missing_required() -> None:
    '''
    Validation fails when required fields (name or kind) are missing on Type.
    '''
    
    with pytest.raises(Exception):
        Type(kind=TypeKind.STR, subtype=None, params=[])  # missing name

    with pytest.raises(Exception):
        Type(name='str', subtype=None, params=[])  # missing kind

# ** test: param_list_creation_and_validation
def test_param_list_creation_and_validation(single_param: ParamList, two_params: ParamList) -> None:
    '''
    Single and chained ParamList instances are created correctly.
    
    :param single_param: Fixture for a single parameter.
    :param two_params: Fixture for a chained parameter list.
    '''
    
    assert single_param.name == 'id'
    assert single_param.type.kind == TypeKind.STR
    assert single_param.required is True

    assert two_params.name == 'name'
    assert two_params.next.name == 'id'

# ** test: param_list_validation_missing_required
def test_param_list_validation_missing_required() -> None:
    '''
    ParamList validation fails when required fields (name and type) are missing.
    '''
    
    with pytest.raises(Exception):
        ParamList(required=False, default=None, next=None)  # missing name

# ** test: declaration_creation_and_validation
def test_declaration_creation_and_validation(basic_declaration: Declaration) -> None:
    '''
    Declaration with minimal required fields is created and validated.
    
    :param basic_declaration: Fixture providing a minimal declaration.
    '''
    
    assert basic_declaration.name == 'error_service'
    assert basic_declaration.type.kind == TypeKind.STR
    assert basic_declaration.metadata == {}

# ** test: declaration_with_optional_fields
def test_declaration_with_optional_fields(
    simple_string_type: Type,
    simple_expression_int: Expression,
    simple_statement_expr: Statement
) -> None:
    '''
    Declaration supports all optional fields (doc_string, value, code, next).
    
    :param simple_string_type: Fixture for the declaration type.
    :param simple_expression_int: Fixture for an expression value.
    :param simple_statement_expr: Fixture for a statement code block.
    '''
    
    decl = Declaration(
        name='calculator_result',
        type=simple_string_type,
        metadata={'role': 'return_value'},
        doc_string='Stores the result of a calculation.',
        value=simple_expression_int,
        code=simple_statement_expr,
        next=None
    )
    assert decl.doc_string is not None
    assert decl.value is not None
    assert decl.code is not None
    assert decl.metadata is not None

# ** test: declaration_validation_missing_required
def test_declaration_validation_missing_required(simple_string_type: Type) -> None:
    '''
    Declaration validation fails when required fields (name or type) are missing.
    
    :param simple_string_type: Fixture providing a type for testing.
    '''
    
    with pytest.raises(Exception):
        Declaration(
            type=simple_string_type,
            metadata={},
            doc_string=None,
            value=None,
            code=None,
            next=None
        )  # missing name

    # Note: Declaration.type is Optional, so omitting it does not raise.

# ** test: expression_creation_and_validation
def test_expression_creation_and_validation(
    simple_expression_name: Expression,
    binary_add_expression: Expression
) -> None:
    '''
    Simple name expression and binary add expression are created correctly.
    
    :param simple_expression_name: Fixture for a name expression.
    :param binary_add_expression: Fixture for a binary add expression.
    '''
    
    assert simple_expression_name.kind == ExprKind.NAME
    assert simple_expression_name.name == 'error_service'

    assert binary_add_expression.kind == ExprKind.ADD
    assert binary_add_expression.left is not None
    assert binary_add_expression.right is not None

# ** test: expression_all_kinds_accepted
def test_expression_all_kinds_accepted() -> None:
    '''
    Every kind defined in ExprKind is accepted by the model.
    '''
    
    for kind in ExprKind:
        e = Expression(
            kind=kind,
            value=None,
            name=None,
            left=None,
            right=None
        )

# ** test: statement_creation_and_validation
def test_statement_creation_and_validation(
    simple_statement_expr: Statement,
    simple_statement_decl: Statement
) -> None:
    '''
    Statement kinds "expr" and "decl" are created correctly.
    
    :param simple_statement_expr: Fixture for an expression statement.
    :param simple_statement_decl: Fixture for a declaration statement.
    '''
    
    assert simple_statement_expr.kind == StatementKind.EXPR
    assert simple_statement_expr.init_expr is not None

    assert simple_statement_decl.kind == StatementKind.DECL
    assert simple_statement_decl.decl is not None

# ** test: statement_all_kinds_accepted
def test_statement_all_kinds_accepted() -> None:
    '''
    Every kind defined in StatementKind is accepted by the model.
    '''
    
    for kind in StatementKind:
        s = Statement(
            kind=kind,
            decl=None,
            inner_expr=None,
            expr=None,
            next_expr=None,
            body=None,
            else_body=None,
            next=None
        )

# ** test: recursive_structures_work
def test_recursive_structures_work(simple_string_type: Type, simple_expression_int: Expression) -> None:
    '''
    Deep recursion works across Declaration.next, Statement.next, Expression.left/right, etc.
    
    :param simple_string_type: Fixture providing a type for declarations.
    :param simple_expression_int: Fixture providing an integer expression for testing trees.
    '''
    
    # Declaration chain
    decl1 = Declaration(
        name='d1',
        type=simple_string_type,
        metadata={},
        doc_string=None,
        value=None,
        code=None,
        next=None
    )
    decl2 = Declaration(
        name='d2',
        type=simple_string_type,
        metadata={},
        doc_string=None,
        value=None,
        code=None,
        next=decl1
    )

    # Statement chain
    stmt1 = Statement(
        kind=StatementKind.EXPR,
        decl=None,
        inner_expr=None,
        expr=None,
        next_expr=None,
        body=None,
        else_body=None,
        next=None
    )
    stmt2 = Statement(
        kind=StatementKind.BLOCK,
        decl=None,
        inner_expr=None,
        expr=None,
        next_expr=None,
        body=None,
        else_body=None,
        next=stmt1
    )

    # Expression tree
    expr = Expression(
        kind=ExprKind.ADD,
        value=None,
        name=None,
        left=simple_expression_int,
        right=simple_expression_int
    )

    assert decl2.next is not None
    assert stmt2.next is not None
    assert expr.left is not None
    assert expr.right is not None