"""Utils – IRGenerator and DocstringParser Tests"""

# *** imports

# ** infra
import pytest

# ** app
from ..ir import DocstringParser, IRGenerator
from ...domain.ast import (
    TypeKind, ExprKind, StatementKind,
    Type, ParamList, Expression, Declaration, Statement,
)
from ...mappers.ast import (
    DeclarationAggregate as Decl,
    StatementAggregate as Stmt,
    ExpressionAggregate as Expr,
    TypeAggregate as TAgg,
    ParamListAggregate as ParamAgg,
)

# *** fixtures

# ** fixture: ir_generator
@pytest.fixture
def ir_generator() -> IRGenerator:
    '''
    Returns a fresh IRGenerator instance.

    :return: An IRGenerator.
    :rtype: IRGenerator
    '''

    return IRGenerator()


# ** fixture: rst_docstring
@pytest.fixture
def rst_docstring() -> str:
    '''
    Returns a raw RST-formatted triple-quoted docstring.

    :return: A sample RST docstring string.
    :rtype: str
    '''

    return '"""Execute the operation.\n\n:param a: The first operand.\n:param b: The second operand.\n:return: The computed result.\n"""'


# ** fixture: minimal_event_ast
@pytest.fixture
def minimal_event_ast() -> Decl:
    '''
    Returns a minimal DeclarationAggregate representing a module with one event
    that has a single execute method returning str with no params beyond self+kwargs.

    :return: A minimal module declaration aggregate.
    :rtype: Decl
    '''

    # Build the execute function type: (self, **kwargs) -> str
    self_param = ParamAgg(name='self', type=TAgg(kind=TypeKind.UNKNOWN), required=True)
    kwargs_param = ParamAgg(name='kwargs', type=TAgg(kind=TypeKind.DICT), required=False)
    self_param.set_next(kwargs_param)

    execute_type = TAgg.new_func_type(
        params=self_param,
        return_type=TAgg(kind=TypeKind.STR),
    )

    # Build the return statement: return 'pong'
    return_stmt = Stmt(
        kind=StatementKind.RETURN,
        expr=Expr(kind=ExprKind.STR_VAL, value="'pong'"),
    )
    snippet_stmt = Stmt(kind=StatementKind.SNIPPET, body=return_stmt)

    # Build the execute declaration.
    execute_decl = Decl(
        name='execute',
        type=execute_type,
        doc_string='"""Return a static string."""',
        code=snippet_stmt,
    )
    execute_stmt = Stmt(kind=StatementKind.DECL, decl=execute_decl)

    # Wrap execute in an ARTIFACT_MEMBER.
    method_member = Decl(
        name='method',
        type=TAgg(kind=TypeKind.ARTIFACT),
        metadata={'type': 'ARTIFACT_MEMBER'},
        code=execute_stmt,
    )
    method_stmt = Stmt(kind=StatementKind.DECL, decl=method_member)

    # Build the Ping class.
    ping_decl = Decl(
        name='Ping',
        type=TAgg.new_class_type(name='Ping', subclasses=TAgg.new_class_type(name='DomainEvent')),
        doc_string='"""A minimal event."""',
        code=method_stmt,
    )
    ping_stmt = Stmt(kind=StatementKind.DECL, decl=ping_decl)

    # Wrap class in event ** artifact.
    event_artifact_decl = Decl(
        name='event: ping',
        type=TAgg(kind=TypeKind.ARTIFACT),
        metadata={'type': '**'},
    )
    event_artifact_stmt = Stmt(
        kind=StatementKind.ARTIFACT,
        decl=event_artifact_decl,
        body=ping_stmt,
    )

    # Build *** events group.
    events_decl = Decl(
        name='events',
        type=TAgg(kind=TypeKind.ARTIFACT),
        metadata={'type': '***'},
    )
    events_stmt = Stmt(
        kind=StatementKind.ARTIFACT,
        decl=events_decl,
        body=event_artifact_stmt,
    )

    # Build *** imports group with one import.
    import_expr = Expr(kind=ExprKind.NAME, name='DomainEvent')
    import_stmt = Stmt(
        kind=StatementKind.IMPORT_FROM,
        init_expr=Expr(kind=ExprKind.NAME, name='.settings'),
        expr=import_expr,
    )
    app_artifact_decl = Decl(
        name='app',
        type=TAgg(kind=TypeKind.ARTIFACT),
        metadata={'type': '**'},
    )
    app_artifact_stmt = Stmt(
        kind=StatementKind.ARTIFACT,
        decl=app_artifact_decl,
        body=import_stmt,
    )
    imports_decl = Decl(
        name='imports',
        type=TAgg(kind=TypeKind.ARTIFACT),
        metadata={'type': '***'},
    )
    imports_stmt = Stmt(
        kind=StatementKind.ARTIFACT,
        decl=imports_decl,
        body=app_artifact_stmt,
    )

    # Chain imports → events at the top level.
    imports_stmt.next = events_stmt

    # Build the module root.
    module = Decl(
        name='pass_minimal_event',
        doc_string='"""Minimal test module."""',
        code=imports_stmt,
    )
    return module


# *** tests — DocstringParser

# ** test: docstring_parser_strip_triple_double
def test_docstring_parser_strip_triple_double() -> None:
    '''
    Test that DocstringParser.strip removes triple-double-quote delimiters.
    '''

    result = DocstringParser.strip('"""Hello, world."""')
    assert result == 'Hello, world.'


# ** test: docstring_parser_strip_triple_single
def test_docstring_parser_strip_triple_single() -> None:
    '''
    Test that DocstringParser.strip removes triple-single-quote delimiters.
    '''

    result = DocstringParser.strip("'''Hello, world.'''")
    assert result == 'Hello, world.'


# ** test: docstring_parser_strip_empty
def test_docstring_parser_strip_empty() -> None:
    '''
    Test that DocstringParser.strip returns empty string for falsy input.
    '''

    assert DocstringParser.strip('') == ''
    assert DocstringParser.strip(None) == ''


# ** test: docstring_parser_parse_param_descriptions
def test_docstring_parser_parse_param_descriptions(rst_docstring: str) -> None:
    '''
    Test extraction of :param name: entries from an RST docstring.

    :param rst_docstring: The sample RST docstring.
    :type rst_docstring: str
    '''

    result = DocstringParser.parse_param_descriptions(rst_docstring)
    assert 'a' in result
    assert result['a'] == 'The first operand.'
    assert 'b' in result
    assert result['b'] == 'The second operand.'


# ** test: docstring_parser_parse_param_descriptions_empty
def test_docstring_parser_parse_param_descriptions_empty() -> None:
    '''
    Test that parse_param_descriptions returns empty dict for a single-line docstring.
    '''

    result = DocstringParser.parse_param_descriptions('"""Return a value."""')
    assert result == {}


# ** test: docstring_parser_parse_return_descriptions
def test_docstring_parser_parse_return_descriptions(rst_docstring: str) -> None:
    '''
    Test extraction of :return: entries from an RST docstring.

    :param rst_docstring: The sample RST docstring.
    :type rst_docstring: str
    '''

    result = DocstringParser.parse_return_descriptions(rst_docstring)
    assert len(result) == 1
    assert result[0] == 'The computed result.'


# ** test: docstring_parser_parse_return_descriptions_empty
def test_docstring_parser_parse_return_descriptions_empty() -> None:
    '''
    Test that parse_return_descriptions returns empty list for a plain docstring.
    '''

    result = DocstringParser.parse_return_descriptions('"""Just a description."""')
    assert result == []


# *** tests — IRGenerator

# ** test: ir_generator_encode_expr_add
def test_ir_generator_encode_expr_add(ir_generator: IRGenerator) -> None:
    '''
    Test encode_expr for an addition expression.

    :param ir_generator: The generator under test.
    :type ir_generator: IRGenerator
    '''

    expr = Expr(
        kind=ExprKind.ADD,
        left=Expr(kind=ExprKind.STR_VAL, value='a'),
        right=Expr(kind=ExprKind.STR_VAL, value='b'),
    )
    result = ir_generator.encode_expr(expr)
    assert result == 'Add(a, b)'


# ** test: ir_generator_encode_expr_return_name
def test_ir_generator_encode_expr_return_name(ir_generator: IRGenerator) -> None:
    '''
    Test encode_stmt for a return statement with a name expression.

    :param ir_generator: The generator under test.
    :type ir_generator: IRGenerator
    '''

    stmt = Stmt(
        kind=StatementKind.RETURN,
        expr=Expr(kind=ExprKind.NAME, name='self.pong'),
    )
    result = ir_generator.encode_stmt(stmt)
    assert result == 'Return(self.pong)'


# ** test: ir_generator_encode_expr_exponentiation
def test_ir_generator_encode_expr_exponentiation(ir_generator: IRGenerator) -> None:
    '''
    Test encode_expr for the exponentiation parser hack (kind=name, value="**").

    :param ir_generator: The generator under test.
    :type ir_generator: IRGenerator
    '''

    expr = Expr(
        kind=ExprKind.NAME,
        value='**',
        left=Expr(kind=ExprKind.STR_VAL, value='a'),
        right=Expr(kind=ExprKind.STR_VAL, value='b'),
    )
    result = ir_generator.encode_expr(expr)
    assert result == 'Exp(a, b)'


# ** test: ir_generator_get_type_name_primitive
def test_ir_generator_get_type_name_primitive(ir_generator: IRGenerator) -> None:
    '''
    Test get_type_name for a primitive str type.

    :param ir_generator: The generator under test.
    :type ir_generator: IRGenerator
    '''

    t = TAgg(kind=TypeKind.STR)
    assert ir_generator.get_type_name(t) == 'str'


# ** test: ir_generator_get_type_name_class
def test_ir_generator_get_type_name_class(ir_generator: IRGenerator) -> None:
    '''
    Test get_type_name for a class-typed node.

    :param ir_generator: The generator under test.
    :type ir_generator: IRGenerator
    '''

    t = TAgg.new_class_type(name='ErrorService')
    assert ir_generator.get_type_name(t) == 'ErrorService'


# ** test: ir_generator_generate_minimal_event
def test_ir_generator_generate_minimal_event(
        ir_generator: IRGenerator,
        minimal_event_ast: Decl,
    ) -> None:
    '''
    Test full IR generation from a minimal event AST fixture.

    :param ir_generator: The generator under test.
    :type ir_generator: IRGenerator
    :param minimal_event_ast: The module AST fixture.
    :type minimal_event_ast: Decl
    '''

    # Generate the IR from the fixture AST.
    ir = ir_generator.generate(minimal_event_ast)

    # Verify top-level fields.
    assert ir.name == 'pass_minimal_event'
    assert ir.description == 'Minimal test module.'

    # Verify imports were extracted.
    assert len(ir.import_groups.groups) == 1
    assert ir.import_groups.groups[0].category == 'app'
    assert ir.import_groups.groups[0].imports[0].symbol == 'DomainEvent'

    # Verify the event was extracted.
    assert len(ir.events.events) == 1
    event = ir.events.events[0]
    assert event.class_name == 'Ping'
    assert event.doc_string == 'A minimal event.'
    assert event.execute.name == 'execute'
    assert len(event.execute.returns.returns) == 1
    assert event.execute.returns.returns[0].type_name == 'str'


# ** test: ir_generator_generate_keter_output
def test_ir_generator_generate_keter_output(
        ir_generator: IRGenerator,
        minimal_event_ast: Decl,
    ) -> None:
    '''
    Test that generate() produces a valid keter string via to_keter().

    :param ir_generator: The generator under test.
    :type ir_generator: IRGenerator
    :param minimal_event_ast: The module AST fixture.
    :type minimal_event_ast: Decl
    '''

    # Generate and serialize.
    ir = ir_generator.generate(minimal_event_ast)
    keter = ir.to_keter()

    # Verify key structural elements appear in the output.
    assert 'EventGroup(pass_minimal_event' in keter
    assert 'ImportGroup(app' in keter
    assert 'Event(Ping' in keter
    assert 'Execute(execute' in keter
    assert 'Return("str:' in keter
