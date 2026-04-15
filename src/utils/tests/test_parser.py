"""Parser Utility Tests"""

# *** imports

# ** infra
import pytest

# ** app
from ..parser import TiferetParser, ParserBase, TokenStream
from ...mappers import Tok
from ...domain import TypeKind, ExprKind, StatementKind

# *** helpers

def tok(type, value=None, lineno=1, lexpos=0):
    '''Create a TokenAggregate for test token streams.'''
    return Tok.new(
        type=type,
        value=value if value is not None else type,
        lineno=lineno,
        lexpos=lexpos,
    )


def collect(node, attr='next'):
    '''Walk a linked list via `attr` and return a flat Python list.'''
    items = []
    while node:
        items.append(node)
        node = getattr(node, attr, None)
    return items


# -- AST navigation shortcuts --

def get_group(module, idx=0):
    '''Return the idx-th group statement from a parsed module.'''
    return collect(module.code)[idx]


def get_section(module, g=0, s=0):
    '''Return the s-th section from the g-th group.'''
    return collect(get_group(module, g).body)[s]


def get_class_decl(module, g=0, s=0):
    '''Return the class declaration inside a section.'''
    return get_section(module, g, s).body.decl


def get_member(module, idx=0, g=0, s=0):
    '''Return the idx-th member declaration from the first class.'''
    cls = get_class_decl(module, g, s)
    return collect(cls.code.decl)[idx]


def get_func_decl(module, member_idx=0):
    '''Return the function/method declaration inside a member.'''
    member = get_member(module, member_idx)
    return member.code.decl


# -- Token stream builders --

def make_event_module(member_tokens, cls_name='Sample', base='DomainEvent',
                      cls_doc=None):
    '''Build a complete parseable token stream wrapping member_tokens in
    events > section > class.'''
    tokens = [
        tok('ARTIFACT_START', '# *** events'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_SECTION', '# ** event: sample'),
        tok('NEWLINE', '\n'),
        tok('CLASS', 'class'),
        tok('IDENTIFIER', cls_name),
        tok('LPAREN', '('),
        tok('IDENTIFIER', base),
        tok('RPAREN', ')'),
        tok('COLON', ':'),
        tok('NEWLINE', '\n'),
        tok('INDENT', ''),
    ]
    if cls_doc:
        tokens.extend([
            tok('DOCSTRING', cls_doc),
            tok('NEWLINE', '\n'),
        ])
    tokens.extend(member_tokens)
    tokens.append(tok('DEDENT', ''))
    return tokens


def make_method_tokens(name='execute', params=None, body=None,
                       ret=None, doc=None, member_kind='method'):
    '''Build tokens for a single method member (ARTIFACT_MEMBER through DEDENT).'''
    header = '# * init' if member_kind == 'init' else f'# * {member_kind}: {name}'
    toks = [
        tok('ARTIFACT_MEMBER', header),
        tok('NEWLINE', '\n'),
        tok('DEF', 'def'),
        tok('INIT' if name == '__init__' else 'IDENTIFIER', name),
        tok('LPAREN', '('),
        tok('SELF', 'self'),
    ]
    if params:
        toks.append(tok('COMMA', ','))
        toks.extend(params)
    toks.append(tok('RPAREN', ')'))
    if ret:
        toks.extend(ret)
    toks.extend([
        tok('COLON', ':'),
        tok('NEWLINE', '\n'),
        tok('INDENT', ''),
    ])
    if doc:
        toks.extend([tok('DOCSTRING', doc), tok('NEWLINE', '\n')])
    if body:
        toks.extend(body)
    else:
        # default: return result
        toks.extend([
            tok('RETURN', 'return'),
            tok('IDENTIFIER', 'result'),
            tok('NEWLINE', '\n'),
        ])
    toks.append(tok('DEDENT', ''))
    return toks


# *** fixtures

# ** fixture: parser
@pytest.fixture
def parser() -> TiferetParser:
    '''Create a fresh TiferetParser instance for each test.'''

    return TiferetParser()

# *** tests — base & helpers

# ** test: instantiation
def test_instantiation(parser: TiferetParser) -> None:
    '''TiferetParser can be instantiated and exposes the PLY parser.'''

    assert parser is not None
    assert parser.parser_service is not None


# ** test: implements_parser_service
def test_implements_parser_service(parser: TiferetParser) -> None:
    '''TiferetParser is an instance of ParserService.'''

    from ...interfaces import ParserService
    assert isinstance(parser, ParserService)


# ** test: token_stream_adapter
def test_token_stream_adapter() -> None:
    '''TokenStream yields PLY-compatible tokens then None.'''

    tokens = [tok('IDENTIFIER', 'foo'), tok('NEWLINE', '\n')]
    stream = TokenStream(tokens)

    first = stream.token()
    assert first.type == 'IDENTIFIER'
    assert first.value == 'foo'
    assert first.lineno == 1
    assert first.lexpos == 0

    second = stream.token()
    assert second.type == 'NEWLINE'

    assert stream.token() is None


# ** test: parse_artifact_header
def test_parse_artifact_header() -> None:
    '''parse_artifact_header extracts (name, type) from artifact header tokens.'''

    # Simple group headers.
    assert ParserBase.parse_artifact_header('# *** imports') == ('imports', '***')
    assert ParserBase.parse_artifact_header('# *** events') == ('events', '***')

    # Simple section headers (no colon).
    assert ParserBase.parse_artifact_header('# ** app') == ('app', '**')
    assert ParserBase.parse_artifact_header('# ** core') == ('core', '**')

    # Colon-separated section headers.
    assert ParserBase.parse_artifact_header('# ** event: ping') == ('ping', '** event')
    assert ParserBase.parse_artifact_header('# ** model: error') == ('error', '** model')


# ** test: parse_member_kind
def test_parse_member_kind() -> None:
    '''parse_member_kind extracts kind from ARTIFACT_MEMBER values.'''

    assert ParserBase.parse_member_kind('# * method: execute') == 'method'
    assert ParserBase.parse_member_kind('# * attribute: service') == 'attribute'
    assert ParserBase.parse_member_kind('# * init') == 'init'
    assert ParserBase.parse_member_kind('# * method: execute (static)') == 'method'


# ** test: get_attribute_type_primitives
def test_get_attribute_type_primitives() -> None:
    '''get_attribute_type maps primitive names to TypeKinds.'''

    assert ParserBase.get_attribute_type('int').kind == TypeKind.INT
    assert ParserBase.get_attribute_type('str').kind == TypeKind.STR
    assert ParserBase.get_attribute_type('float').kind == TypeKind.FLOAT
    assert ParserBase.get_attribute_type('bool').kind == TypeKind.BOOL
    assert ParserBase.get_attribute_type('list').kind == TypeKind.LIST
    assert ParserBase.get_attribute_type('dict').kind == TypeKind.DICT


# ** test: get_attribute_type_class_fallback
def test_get_attribute_type_class_fallback() -> None:
    '''get_attribute_type returns CLASS for unrecognized names.'''

    t = ParserBase.get_attribute_type('ErrorService')
    assert t.kind == TypeKind.CLASS


# *** tests — imports

# ** test: parse_from_import
def test_parse_from_import(parser: TiferetParser) -> None:
    '''Parse `from typing import Any` inside an imports group.'''

    tokens = [
        tok('ARTIFACT_IMPORTS_START', '# *** imports'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_IMPORT_GROUP', '# ** core'),
        tok('NEWLINE', '\n'),
        tok('FROM', 'from'),
        tok('IDENTIFIER', 'typing'),
        tok('IMPORT', 'import'),
        tok('IDENTIFIER', 'Any'),
        tok('NEWLINE', '\n'),
    ]
    module = parser.parse('test', tokens)

    # Module
    assert module.name == '__main__'

    # Group header
    group = get_group(module)
    assert group.kind == StatementKind.ARTIFACT
    assert group.decl.name == 'imports'

    # Section header
    section = get_section(module)
    assert section.decl.name == 'core'

    # Import statement
    stmt = section.body
    assert stmt.kind == StatementKind.IMPORT_FROM
    assert stmt.init_expr.kind == ExprKind.NAME
    assert stmt.init_expr.name == 'typing'
    assert stmt.expr.kind == ExprKind.NAME
    assert stmt.expr.name == 'Any'


# ** test: parse_plain_import
def test_parse_plain_import(parser: TiferetParser) -> None:
    '''Parse `import os` inside an imports group.'''

    tokens = [
        tok('ARTIFACT_IMPORTS_START', '# *** imports'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_IMPORT_GROUP', '# ** core'),
        tok('NEWLINE', '\n'),
        tok('IMPORT', 'import'),
        tok('IDENTIFIER', 'os'),
        tok('NEWLINE', '\n'),
    ]
    module = parser.parse('test', tokens)
    stmt = get_section(module).body
    assert stmt.kind == StatementKind.IMPORT
    assert stmt.expr.name == 'os'


# ** test: parse_import_as
def test_parse_import_as(parser: TiferetParser) -> None:
    '''Parse `import os as operating_system`.'''

    tokens = [
        tok('ARTIFACT_IMPORTS_START', '# *** imports'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_IMPORT_GROUP', '# ** core'),
        tok('NEWLINE', '\n'),
        tok('IMPORT', 'import'),
        tok('IDENTIFIER', 'os'),
        tok('AS', 'as'),
        tok('IDENTIFIER', 'operating_system'),
        tok('NEWLINE', '\n'),
    ]
    module = parser.parse('test', tokens)
    expr = get_section(module).body.expr
    assert expr.kind == ExprKind.IMPORT_AS
    assert expr.left.name == 'os'
    assert expr.right.name == 'operating_system'


# ** test: parse_multi_import
def test_parse_multi_import(parser: TiferetParser) -> None:
    '''Parse `from typing import Any, List`.'''

    tokens = [
        tok('ARTIFACT_IMPORTS_START', '# *** imports'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_IMPORT_GROUP', '# ** core'),
        tok('NEWLINE', '\n'),
        tok('FROM', 'from'),
        tok('IDENTIFIER', 'typing'),
        tok('IMPORT', 'import'),
        tok('IDENTIFIER', 'Any'),
        tok('COMMA', ','),
        tok('IDENTIFIER', 'List'),
        tok('NEWLINE', '\n'),
    ]
    module = parser.parse('test', tokens)
    expr = get_section(module).body.expr
    assert expr.kind == ExprKind.IMPORT_MULTI
    assert expr.left.name == 'Any'
    assert expr.right.name == 'List'


# ** test: parse_dotted_from_import
def test_parse_dotted_from_import(parser: TiferetParser) -> None:
    '''Parse `from ..module import Foo` with relative dots.'''

    tokens = [
        tok('ARTIFACT_IMPORTS_START', '# *** imports'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_IMPORT_GROUP', '# ** app'),
        tok('NEWLINE', '\n'),
        tok('FROM', 'from'),
        tok('DOT', '.'),
        tok('DOT', '.'),
        tok('IDENTIFIER', 'module'),
        tok('IMPORT', 'import'),
        tok('IDENTIFIER', 'Foo'),
        tok('NEWLINE', '\n'),
    ]
    module = parser.parse('test', tokens)
    stmt = get_section(module).body
    assert stmt.kind == StatementKind.IMPORT_FROM
    assert stmt.init_expr.name == '..module'


# ** test: parse_multiple_import_stmts
def test_parse_multiple_import_stmts(parser: TiferetParser) -> None:
    '''Two import statements in one section form a linked import block.'''

    tokens = [
        tok('ARTIFACT_IMPORTS_START', '# *** imports'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_IMPORT_GROUP', '# ** core'),
        tok('NEWLINE', '\n'),
        tok('IMPORT', 'import'),
        tok('IDENTIFIER', 'os'),
        tok('NEWLINE', '\n'),
        tok('FROM', 'from'),
        tok('IDENTIFIER', 'typing'),
        tok('IMPORT', 'import'),
        tok('IDENTIFIER', 'Any'),
        tok('NEWLINE', '\n'),
    ]
    module = parser.parse('test', tokens)
    stmts = collect(get_section(module).body)
    assert len(stmts) == 2
    assert stmts[0].kind == StatementKind.IMPORT
    assert stmts[1].kind == StatementKind.IMPORT_FROM


# *** tests — attribute declarations

# ** test: parse_attr_plain
def test_parse_attr_plain(parser: TiferetParser) -> None:
    '''Parse `# * attribute: service` / `service` (no type).'''

    tokens = make_event_module([
        tok('ARTIFACT_MEMBER', '# * attribute: service'),
        tok('NEWLINE', '\n'),
        tok('IDENTIFIER', 'service'),
        tok('NEWLINE', '\n'),
    ])
    module = parser.parse('test', tokens)
    member = get_member(module)
    assert member.name == 'attribute'

    attr = member.code.decl
    assert attr.name == 'service'
    assert attr.type is None


# ** test: parse_attr_typed
def test_parse_attr_typed(parser: TiferetParser) -> None:
    '''Parse `service: ErrorService` with a class type annotation.'''

    tokens = make_event_module([
        tok('ARTIFACT_MEMBER', '# * attribute: service'),
        tok('NEWLINE', '\n'),
        tok('IDENTIFIER', 'service'),
        tok('COLON', ':'),
        tok('IDENTIFIER', 'ErrorService'),
        tok('NEWLINE', '\n'),
    ])
    module = parser.parse('test', tokens)
    attr = get_member(module).code.decl
    assert attr.name == 'service'
    assert attr.type.kind == TypeKind.CLASS


# ** test: parse_attr_union_type
def test_parse_attr_union_type(parser: TiferetParser) -> None:
    '''Parse `value: int | str` union attribute type.'''

    tokens = make_event_module([
        tok('ARTIFACT_MEMBER', '# * attribute: value'),
        tok('NEWLINE', '\n'),
        tok('IDENTIFIER', 'value'),
        tok('COLON', ':'),
        tok('IDENTIFIER', 'int'),
        tok('PIPE', '|'),
        tok('IDENTIFIER', 'str'),
        tok('NEWLINE', '\n'),
    ])
    module = parser.parse('test', tokens)
    attr = get_member(module).code.decl
    assert attr.type.kind == TypeKind.INT
    assert attr.type.subtype.kind == TypeKind.STR


# *** tests — method declarations & parameters

# ** test: parse_method_self_only
def test_parse_method_self_only(parser: TiferetParser) -> None:
    '''Parse `def execute(self):` with no extra params.'''

    tokens = make_event_module(make_method_tokens())
    module = parser.parse('test', tokens)

    func = get_func_decl(module)
    assert func.name == 'execute'
    assert func.type.kind == TypeKind.FUNC

    # Param list: self only
    params = collect(func.type.params)
    assert len(params) == 1
    assert params[0].name == 'self'

    # Return type: None (empty annotation)
    assert func.type.return_type.kind == TypeKind.NONE


# ** test: parse_method_with_typed_param
def test_parse_method_with_typed_param(parser: TiferetParser) -> None:
    '''Parse `def execute(self, id: str):` with a typed parameter.'''

    param_tokens = [
        tok('IDENTIFIER', 'id'),
        tok('COLON', ':'),
        tok('IDENTIFIER', 'str'),
    ]
    tokens = make_event_module(make_method_tokens(params=param_tokens))
    module = parser.parse('test', tokens)

    params = collect(get_func_decl(module).type.params)
    assert len(params) == 2
    assert params[0].name == 'self'
    assert params[1].name == 'id'
    assert params[1].type.kind == TypeKind.STR


# ** test: parse_method_param_default
def test_parse_method_param_default(parser: TiferetParser) -> None:
    '''Parse `def execute(self, x: str = 'hello'):` with a default value.'''

    param_tokens = [
        tok('IDENTIFIER', 'x'),
        tok('COLON', ':'),
        tok('IDENTIFIER', 'str'),
        tok('EQUALS', '='),
        tok('STRING_LITERAL', "'hello'"),
    ]
    tokens = make_event_module(make_method_tokens(params=param_tokens))
    module = parser.parse('test', tokens)

    params = collect(get_func_decl(module).type.params)
    assert params[1].name == 'x'
    assert params[1].type.kind == TypeKind.STR
    assert params[1].default is not None
    assert params[1].default.kind == ExprKind.STR_VAL
    assert params[1].required is False


# ** test: parse_method_args_kwargs
def test_parse_method_args_kwargs(parser: TiferetParser) -> None:
    '''Parse `def execute(self, *args, **kwargs):`.'''

    param_tokens = [
        tok('STAR', '*'),
        tok('IDENTIFIER', 'args'),
        tok('COMMA', ','),
        tok('DOUBLESTAR', '**'),
        tok('IDENTIFIER', 'kwargs'),
    ]
    tokens = make_event_module(make_method_tokens(params=param_tokens))
    module = parser.parse('test', tokens)

    params = collect(get_func_decl(module).type.params)
    assert len(params) == 3
    assert params[1].name == 'args'
    assert params[1].type.kind == TypeKind.LIST
    assert params[2].name == 'kwargs'
    assert params[2].type.kind == TypeKind.DICT


# ** test: parse_method_return_type
def test_parse_method_return_type(parser: TiferetParser) -> None:
    '''Parse `def execute(self) -> str:` with a return annotation.'''

    ret_tokens = [tok('ARROW', '->'), tok('IDENTIFIER', 'str')]
    tokens = make_event_module(make_method_tokens(ret=ret_tokens))
    module = parser.parse('test', tokens)

    func = get_func_decl(module)
    assert func.type.return_type.kind == TypeKind.STR


# ** test: parse_method_return_union_type
def test_parse_method_return_union_type(parser: TiferetParser) -> None:
    '''Parse `-> int | str` union return annotation.'''

    ret_tokens = [
        tok('ARROW', '->'),
        tok('IDENTIFIER', 'int'),
        tok('PIPE', '|'),
        tok('IDENTIFIER', 'str'),
    ]
    tokens = make_event_module(make_method_tokens(ret=ret_tokens))
    module = parser.parse('test', tokens)

    ret = get_func_decl(module).type.return_type
    assert ret.kind == TypeKind.INT
    assert ret.return_type.kind == TypeKind.STR


# ** test: parse_method_docstring
def test_parse_method_docstring(parser: TiferetParser) -> None:
    '''Method docstring is captured in the function declaration.'''

    tokens = make_event_module(
        make_method_tokens(doc='"""Execute the event."""')
    )
    module = parser.parse('test', tokens)
    assert get_func_decl(module).doc_string == '"""Execute the event."""'


# ** test: parse_method_init_name
def test_parse_method_init_name(parser: TiferetParser) -> None:
    '''Parse `def __init__(self, svc):` with INIT token.'''

    param_tokens = [tok('IDENTIFIER', 'svc')]
    body_tokens = [
        tok('SELF', 'self'),
        tok('DOT', '.'),
        tok('IDENTIFIER', 'svc'),
        tok('EQUALS', '='),
        tok('IDENTIFIER', 'svc'),
        tok('NEWLINE', '\n'),
    ]
    tokens = make_event_module(
        make_method_tokens(
            name='__init__', params=param_tokens,
            body=body_tokens, member_kind='init',
        )
    )
    module = parser.parse('test', tokens)

    member = get_member(module)
    assert member.name == 'init'

    func = member.code.decl
    assert func.name == '__init__'


# ** test: parse_method_param_union_type
def test_parse_method_param_union_type(parser: TiferetParser) -> None:
    '''Parse `id: int | str` union parameter type.'''

    param_tokens = [
        tok('IDENTIFIER', 'id'),
        tok('COLON', ':'),
        tok('IDENTIFIER', 'int'),
        tok('PIPE', '|'),
        tok('IDENTIFIER', 'str'),
    ]
    tokens = make_event_module(make_method_tokens(params=param_tokens))
    module = parser.parse('test', tokens)

    params = collect(get_func_decl(module).type.params)
    assert params[1].type.kind == TypeKind.INT
    assert params[1].type.subtype.kind == TypeKind.STR


# ** test: parse_method_multiline_params
def test_parse_method_multiline_params(parser: TiferetParser) -> None:
    '''NEWLINE inside param list is absorbed by the param : NEWLINE param rule.'''

    param_tokens = [
        tok('NEWLINE', '\n'),
        tok('IDENTIFIER', 'id'),
        tok('COLON', ':'),
        tok('IDENTIFIER', 'str'),
    ]
    tokens = make_event_module(make_method_tokens(params=param_tokens))
    module = parser.parse('test', tokens)

    params = collect(get_func_decl(module).type.params)
    assert len(params) == 2
    assert params[1].name == 'id'


# *** tests — class definitions

# ** test: parse_class_single_base
def test_parse_class_single_base(parser: TiferetParser) -> None:
    '''Parse `class Sample(DomainEvent):` with one base class.'''

    tokens = make_event_module(make_method_tokens())
    module = parser.parse('test', tokens)

    cls = get_class_decl(module)
    assert cls.name == 'Sample'
    assert cls.type.kind == TypeKind.CLASS
    assert cls.type.name == 'Sample'
    assert cls.type.subtype.name == 'DomainEvent'


# ** test: parse_class_multi_base
def test_parse_class_multi_base(parser: TiferetParser) -> None:
    '''Parse `class Sample(Base, Mixin):` with multiple base classes.'''

    tokens = [
        tok('ARTIFACT_START', '# *** events'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_SECTION', '# ** event: sample'),
        tok('NEWLINE', '\n'),
        tok('CLASS', 'class'),
        tok('IDENTIFIER', 'Sample'),
        tok('LPAREN', '('),
        tok('IDENTIFIER', 'Base'),
        tok('COMMA', ','),
        tok('IDENTIFIER', 'Mixin'),
        tok('RPAREN', ')'),
        tok('COLON', ':'),
        tok('NEWLINE', '\n'),
        tok('INDENT', ''),
        *make_method_tokens(),
        tok('DEDENT', ''),
    ]
    module = parser.parse('test', tokens)
    cls = get_class_decl(module)
    assert cls.type.subtype.name == 'Base'
    assert cls.type.subtype.subtype.name == 'Mixin'


# ** test: parse_class_docstring
def test_parse_class_docstring(parser: TiferetParser) -> None:
    '''Class docstring is captured in the class declaration.'''

    tokens = make_event_module(
        make_method_tokens(),
        cls_doc='"""Sample event."""',
    )
    module = parser.parse('test', tokens)
    assert get_class_decl(module).doc_string == '"""Sample event."""'


# ** test: parse_multiple_members
def test_parse_multiple_members(parser: TiferetParser) -> None:
    '''Class with an attribute member followed by a method member.'''

    attr_tokens = [
        tok('ARTIFACT_MEMBER', '# * attribute: service'),
        tok('NEWLINE', '\n'),
        tok('IDENTIFIER', 'service'),
        tok('COLON', ':'),
        tok('IDENTIFIER', 'ErrorService'),
        tok('NEWLINE', '\n'),
    ]
    method_tokens = make_method_tokens()
    tokens = make_event_module(attr_tokens + method_tokens)
    module = parser.parse('test', tokens)

    members = collect(get_class_decl(module).code.decl)
    assert len(members) == 2
    assert members[0].name == 'attribute'
    assert members[1].name == 'method'


# *** tests — statements & snippets

# ** test: parse_return_identifier
def test_parse_return_identifier(parser: TiferetParser) -> None:
    '''`return result` produces a RETURN statement with a NAME expression.'''

    tokens = make_event_module(make_method_tokens())
    module = parser.parse('test', tokens)

    # Navigate: func.code is snippet_list (first snippet)
    snippet = get_func_decl(module).code
    assert snippet.kind == StatementKind.SNIPPET

    # The snippet body is the return stmt
    ret = snippet.body
    assert ret.kind == StatementKind.RETURN
    assert ret.expr.kind == ExprKind.NAME
    assert ret.expr.name == 'result'


# ** test: parse_return_empty
def test_parse_return_empty(parser: TiferetParser) -> None:
    '''`return` with no expression produces a RETURN statement with None expr.'''

    body = [tok('RETURN', 'return'), tok('NEWLINE', '\n')]
    tokens = make_event_module(make_method_tokens(body=body))
    module = parser.parse('test', tokens)

    ret = get_func_decl(module).code.body
    assert ret.kind == StatementKind.RETURN
    assert ret.expr is None


# ** test: parse_return_bool_literal
def test_parse_return_bool_literal(parser: TiferetParser) -> None:
    '''`return True` produces BOOL_VAL expression.'''

    body = [tok('RETURN', 'return'), tok('TRUE', 'True'), tok('NEWLINE', '\n')]
    tokens = make_event_module(make_method_tokens(body=body))
    module = parser.parse('test', tokens)

    ret = get_func_decl(module).code.body
    assert ret.expr.kind == ExprKind.BOOL_VAL
    assert ret.expr.value == 'True'


# ** test: parse_return_string_literal
def test_parse_return_string_literal(parser: TiferetParser) -> None:
    '''`return 'hello'` produces STR_VAL expression.'''

    body = [
        tok('RETURN', 'return'),
        tok('STRING_LITERAL', "'hello'"),
        tok('NEWLINE', '\n'),
    ]
    tokens = make_event_module(make_method_tokens(body=body))
    module = parser.parse('test', tokens)

    ret = get_func_decl(module).code.body
    assert ret.expr.kind == ExprKind.STR_VAL
    assert ret.expr.value == "'hello'"


# ** test: parse_assign_stmt
def test_parse_assign_stmt(parser: TiferetParser) -> None:
    '''`self.svc = svc` produces an ASSIGN expression statement.'''

    body = [
        tok('SELF', 'self'),
        tok('DOT', '.'),
        tok('IDENTIFIER', 'svc'),
        tok('EQUALS', '='),
        tok('IDENTIFIER', 'svc'),
        tok('NEWLINE', '\n'),
    ]
    tokens = make_event_module(make_method_tokens(body=body))
    module = parser.parse('test', tokens)

    stmt = get_func_decl(module).code.body
    assert stmt.kind == StatementKind.EXPR
    assert stmt.expr.kind == ExprKind.ASSIGN
    assert stmt.expr.left.name == 'self.svc'
    assert stmt.expr.right.name == 'svc'


# ** test: parse_return_operation
def test_parse_return_operation(parser: TiferetParser) -> None:
    '''`return a + b` produces an ADD expression inside a return.'''

    body = [
        tok('RETURN', 'return'),
        tok('IDENTIFIER', 'a'),
        tok('PLUS', '+'),
        tok('IDENTIFIER', 'b'),
        tok('NEWLINE', '\n'),
    ]
    tokens = make_event_module(make_method_tokens(body=body))
    module = parser.parse('test', tokens)

    ret = get_func_decl(module).code.body
    assert ret.kind == StatementKind.RETURN
    assert ret.expr.kind == ExprKind.ADD
    assert ret.expr.left.name == 'a'
    assert ret.expr.right.name == 'b'


# ** test: parse_return_call
def test_parse_return_call(parser: TiferetParser) -> None:
    '''`return foo(x)` produces a CALL expression inside a return.'''

    body = [
        tok('RETURN', 'return'),
        tok('IDENTIFIER', 'foo'),
        tok('LPAREN', '('),
        tok('IDENTIFIER', 'x'),
        tok('RPAREN', ')'),
        tok('NEWLINE', '\n'),
    ]
    tokens = make_event_module(make_method_tokens(body=body))
    module = parser.parse('test', tokens)

    ret = get_func_decl(module).code.body
    assert ret.kind == StatementKind.RETURN
    assert ret.expr.kind == ExprKind.CALL
    assert ret.expr.left.name == 'foo'


# ** test: parse_snippet_with_comment
def test_parse_snippet_with_comment(parser: TiferetParser) -> None:
    '''A LINE_COMMENT heads a snippet; following stmts are in the same snippet body.'''

    body = [
        tok('LINE_COMMENT', '# Do the work.'),
        tok('NEWLINE', '\n'),
        tok('RETURN', 'return'),
        tok('IDENTIFIER', 'result'),
        tok('NEWLINE', '\n'),
    ]
    tokens = make_event_module(make_method_tokens(body=body))
    module = parser.parse('test', tokens)

    snippet = get_func_decl(module).code
    assert snippet.kind == StatementKind.SNIPPET

    # First node in body chain is the comment
    comment = snippet.body
    assert comment.kind == StatementKind.COMMENT
    assert comment.expr.kind == ExprKind.COMMENT
    assert comment.expr.value == '# Do the work.'

    # Next is the return
    ret = comment.next
    assert ret.kind == StatementKind.RETURN


# ** test: parse_multiple_snippets
def test_parse_multiple_snippets(parser: TiferetParser) -> None:
    '''Two comment-headed snippets produce a linked snippet list.'''

    body = [
        # Snippet 1
        tok('LINE_COMMENT', '# Step one.'),
        tok('NEWLINE', '\n'),
        tok('SELF', 'self'),
        tok('DOT', '.'),
        tok('IDENTIFIER', 'x'),
        tok('EQUALS', '='),
        tok('IDENTIFIER', 'val'),
        tok('NEWLINE', '\n'),
        # Snippet 2
        tok('LINE_COMMENT', '# Step two.'),
        tok('NEWLINE', '\n'),
        tok('RETURN', 'return'),
        tok('IDENTIFIER', 'result'),
        tok('NEWLINE', '\n'),
    ]
    tokens = make_event_module(make_method_tokens(body=body))
    module = parser.parse('test', tokens)

    snippets = collect(get_func_decl(module).code)
    assert len(snippets) == 2
    assert snippets[0].kind == StatementKind.SNIPPET
    assert snippets[1].kind == StatementKind.SNIPPET


# *** tests — groups, sections & module

# ** test: parse_empty_module
def test_parse_empty_module(parser: TiferetParser) -> None:
    '''An empty token stream produces a module with no groups.'''

    module = parser.parse('test', [])
    assert module.name == '__main__'
    assert module.code is None


# ** test: parse_two_groups
def test_parse_two_groups(parser: TiferetParser) -> None:
    '''Imports group followed by events group produces two linked groups.'''

    tokens = [
        # Group 1: imports
        tok('ARTIFACT_IMPORTS_START', '# *** imports'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_IMPORT_GROUP', '# ** core'),
        tok('NEWLINE', '\n'),
        tok('FROM', 'from'),
        tok('IDENTIFIER', 'typing'),
        tok('IMPORT', 'import'),
        tok('IDENTIFIER', 'Any'),
        tok('NEWLINE', '\n'),
        # Group 2: events
        *make_event_module(make_method_tokens()),
    ]
    module = parser.parse('test', tokens)
    groups = collect(module.code)
    assert len(groups) == 2
    assert groups[0].decl.name == 'imports'
    assert groups[1].decl.name == 'events'


# ** test: parse_two_sections
def test_parse_two_sections(parser: TiferetParser) -> None:
    '''Two sections inside a single group are linked via next.'''

    tokens = [
        tok('ARTIFACT_IMPORTS_START', '# *** imports'),
        tok('NEWLINE', '\n'),
        # Section 1
        tok('ARTIFACT_IMPORT_GROUP', '# ** core'),
        tok('NEWLINE', '\n'),
        tok('IMPORT', 'import'),
        tok('IDENTIFIER', 'os'),
        tok('NEWLINE', '\n'),
        # Section 2
        tok('ARTIFACT_IMPORT_GROUP', '# ** app'),
        tok('NEWLINE', '\n'),
        tok('FROM', 'from'),
        tok('IDENTIFIER', 'mymod'),
        tok('IMPORT', 'import'),
        tok('IDENTIFIER', 'Foo'),
        tok('NEWLINE', '\n'),
    ]
    module = parser.parse('test', tokens)
    sections = collect(get_group(module).body)
    assert len(sections) == 2
    assert sections[0].decl.name == 'core'
    assert sections[1].decl.name == 'app'


# ** test: parse_module_docstring
def test_parse_module_docstring(parser: TiferetParser) -> None:
    '''A leading DOCSTRING is captured as the module docstring.'''

    tokens = [
        tok('DOCSTRING', '"""My module."""'),
        tok('NEWLINE', '\n'),
        *make_event_module(make_method_tokens()),
    ]
    module = parser.parse('test', tokens)
    assert module.doc_string == '"""My module."""'
    assert module.code is not None


# *** tests — error handling

# ** test: parse_error_unexpected_token
def test_parse_error_unexpected_token(parser: TiferetParser) -> None:
    '''Unexpected token raises SyntaxError with hierarchy terminology.'''

    bad_tokens = [
        tok('ARTIFACT_START', '# *** events'),
        tok('NEWLINE', '\n'),
        tok('DEF', 'def'),
    ]
    with pytest.raises(SyntaxError, match=r'Tiferet artifact hierarchy'):
        parser.parse('test', bad_tokens)


# ** test: parse_error_unexpected_eof
def test_parse_error_unexpected_eof(parser: TiferetParser) -> None:
    '''Unexpected end of input raises SyntaxError with structure terminology.'''

    bad_tokens = [
        tok('ARTIFACT_START', '# *** events'),
    ]
    with pytest.raises(SyntaxError, match=r'Tiferet Domain Event structure'):
        parser.parse('test', bad_tokens)


# ** test: parse_error_class_no_section
def test_parse_error_class_no_section(parser: TiferetParser) -> None:
    '''CLASS directly under a group (missing section) raises SyntaxError.'''

    bad_tokens = [
        tok('ARTIFACT_START', '# *** events'),
        tok('NEWLINE', '\n'),
        tok('CLASS', 'class'),
        tok('IDENTIFIER', 'Foo'),
    ]
    with pytest.raises(SyntaxError):
        parser.parse('test', bad_tokens)
