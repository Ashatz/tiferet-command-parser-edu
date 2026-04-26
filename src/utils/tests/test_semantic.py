"""Tests for Semantic Analysis Builder and Name Resolver"""

# *** imports

# ** infra
import pytest
from tiferet.events import TiferetError

# ** app
from ...domain.semantic import SymbolKind
from ...mappers.ast import (
    DeclarationAggregate as Decl,
    StatementAggregate as Stmt,
    ExpressionAggregate as Expr,
    TypeAggregate as Type,
    ParamListAggregate as ParamList,
)
from ...mappers.semantic import ScopeAggregate
from ..semantic import SymbolTableBuilder, NameResolver
from ..typecheck import TypeChecker

# *** fixtures

# ** fixture: imports_only_ast
@pytest.fixture
def imports_only_ast() -> Decl:
    '''
    Build a module AST matching pass_imports_only.py:
    - imports group with core (Any from typing) and app (DomainEvent, a from .settings; ErrorService from ..interfaces)
    - empty events group
    '''

    # from typing import Any
    import_any = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('typing'),
        import_expr=Expr.new_name_expr('Any'),
    )

    # core group
    core_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('core', '**'),
        section_body=import_any,
    )

    # from .settings import DomainEvent, a
    import_de_a = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('.settings'),
        import_expr=Expr.new_import_expr_multi(
            Expr.new_name_expr('DomainEvent'),
            'a',
        ),
    )

    # from ..interfaces import ErrorService
    import_es = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('..interfaces'),
        import_expr=Expr.new_name_expr('ErrorService'),
    )
    import_de_a.set_next(import_es)

    # app group
    app_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('app', '**'),
        section_body=import_de_a,
    )
    core_group.set_next(app_group)

    # imports section
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=core_group,
    )

    # empty events section
    events_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('events', '***'),
        section_body=None,
    )
    imports_section.set_next(events_section)

    return Decl.new_module_decl(
        name='pass_imports_only',
        code=imports_section,
        doc_string='Tiferet Empty Events Sample',
    )


# ** fixture: minimal_event_ast
@pytest.fixture
def minimal_event_ast() -> Decl:
    '''
    Build a module AST matching pass_minimal_event.py:
    - import DomainEvent from .settings
    - class Ping(DomainEvent) with execute(self, **kwargs) -> str returning 'pong'
    '''

    # Import
    import_de = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('.settings'),
        import_expr=Expr.new_name_expr('DomainEvent'),
    )
    app_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('app', '**'),
        section_body=import_de,
    )
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=app_group,
    )

    # Method: execute(self, **kwargs) -> str
    kwargs_param = ParamList.new_kwargs_param()
    self_param = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)
    self_param.set_next(kwargs_param)

    return_stmt = Stmt.new_return_stmt(
        return_expr=Expr.new_name_or_literal_expr("'pong'"),
    )
    comment_stmt = Stmt.new_comment_stmt(Expr.new_comment_expr('# Return pong.'))
    comment_stmt.set_next(return_stmt)
    snippet = Stmt.new_snippet_stmt(code=comment_stmt)

    execute_decl = Decl.new_func_decl(
        name='execute',
        type=Type.new_func_type(params=self_param, return_type=Type.new(kind='str')),
        doc_string='Return a static response.',
        body=snippet,
    )

    # Member wrapper for execute
    method_member = Decl.new_member_decl(
        name='method',
        member_body=Stmt.new_decl_stmt(execute_decl),
    )

    # Class Ping(DomainEvent)
    ping_class = Decl.new_class_decl(
        name='Ping',
        subclasses=Type.new_class_type(name='DomainEvent'),
        doc_string='A minimal event.',
        members=Stmt.new_decl_stmt(method_member),
    )

    # Event section
    event_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('event: ping', '**'),
        section_body=Stmt.new_decl_stmt(ping_class),
    )
    events_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('events', '***'),
        section_body=event_section,
    )
    imports_section.set_next(events_section)

    return Decl.new_module_decl(name='pass_minimal_event', code=imports_section)


# ** fixture: injection_event_ast
@pytest.fixture
def injection_event_ast() -> Decl:
    '''
    Build a module AST matching pass_minimal_injection_event.py:
    - import DomainEvent from .settings
    - class Ping(DomainEvent) with attribute pong: str, __init__(self, pong: str), execute(self, **kwargs) -> str
    '''

    # Import
    import_de = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('.settings'),
        import_expr=Expr.new_name_expr('DomainEvent'),
    )
    app_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('app', '**'),
        section_body=import_de,
    )
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=app_group,
    )

    # Attribute: pong: str
    pong_attr = Decl.new_attr_decl(name='pong', types=Type.new(kind='str'))
    attr_member = Decl.new_member_decl(
        name='attribute',
        member_body=Stmt.new_decl_stmt(pong_attr),
    )

    # __init__(self, pong: str)
    pong_param = ParamList.new(name='pong', type=Type.new(kind='str'), required=True)
    self_param_init = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)
    self_param_init.set_next(pong_param)

    assign_stmt = Stmt(
        kind='expr',
        expr=Expr(kind='assign', left=Expr.new_name_expr('self.pong'), right=Expr.new_name_or_literal_expr('pong')),
    )
    comment_init = Stmt.new_comment_stmt(Expr.new_comment_expr('# Set the pong attribute.'))
    comment_init.set_next(assign_stmt)
    init_snippet = Stmt.new_snippet_stmt(code=comment_init)

    init_decl = Decl.new_func_decl(
        name='__init__',
        type=Type.new_func_type(params=self_param_init, return_type=Type.new_null_type()),
        doc_string='Initialize with a pong string.',
        body=init_snippet,
    )
    init_member = Decl.new_member_decl(
        name='init',
        member_body=Stmt.new_decl_stmt(init_decl),
    )

    # execute(self, **kwargs) -> str
    kwargs_param = ParamList.new_kwargs_param()
    self_param_exec = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)
    self_param_exec.set_next(kwargs_param)

    return_stmt = Stmt.new_return_stmt(
        return_expr=Expr(kind='str_val', value='self.pong'),
    )
    comment_exec = Stmt.new_comment_stmt(Expr.new_comment_expr('# Return the pong string.'))
    comment_exec.set_next(return_stmt)
    exec_snippet = Stmt.new_snippet_stmt(code=comment_exec)

    execute_decl = Decl.new_func_decl(
        name='execute',
        type=Type.new_func_type(params=self_param_exec, return_type=Type.new(kind='str')),
        doc_string='Return the injected pong string.',
        body=exec_snippet,
    )
    method_member = Decl.new_member_decl(
        name='method',
        member_body=Stmt.new_decl_stmt(execute_decl),
    )

    # Chain members: attribute -> init -> method
    attr_member.next = init_member
    init_member.next = method_member

    # Class Ping
    ping_class = Decl.new_class_decl(
        name='Ping',
        subclasses=Type.new_class_type(name='DomainEvent'),
        doc_string=None,
        members=Stmt.new_decl_stmt(attr_member),
    )

    event_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('event: ping', '**'),
        section_body=Stmt.new_decl_stmt(ping_class),
    )
    events_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('events', '***'),
        section_body=event_section,
    )
    imports_section.set_next(events_section)

    return Decl.new_module_decl(name='pass_minimal_injection_event', code=imports_section)


# ** fixture: multi_operator_ast
@pytest.fixture
def multi_operator_ast() -> Decl:
    '''
    Build a module AST matching pass_multiple_operator_events.py:
    - import DomainEvent from tiferet.events
    - 6 classes (Add, Subtract, Multiply, Divide, Modulus, Exponentiate) each with execute(self, a: int, b: int)
    '''

    # Import
    import_de = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('tiferet.events'),
        import_expr=Expr.new_name_expr('DomainEvent'),
    )
    infra_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('infra', '**'),
        section_body=import_de,
    )
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=infra_group,
    )

    # Helper to build one operator class
    def make_operator_class(class_name: str, return_kind: str) -> Decl:
        b_param = ParamList.new(name='b', type=Type.new(kind='int'), required=True)
        a_param = ParamList.new(name='a', type=Type.new(kind='int'), required=True)
        a_param.set_next(b_param)
        self_param = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)
        self_param.set_next(a_param)

        return_expr = Expr.new_operator_expr('+', Expr.new_name_or_literal_expr('a'), Expr.new_name_or_literal_expr('b'))
        return_stmt = Stmt.new_return_stmt(return_expr=return_expr)
        snippet = Stmt.new_snippet_stmt(code=return_stmt)

        execute_decl = Decl.new_func_decl(
            name='execute',
            type=Type.new_func_type(params=self_param, return_type=Type.new(kind=return_kind)),
            body=snippet,
        )
        method_member = Decl.new_member_decl(
            name='method',
            member_body=Stmt.new_decl_stmt(execute_decl),
        )
        return Decl.new_class_decl(
            name=class_name,
            subclasses=Type.new_class_type(name='DomainEvent'),
            doc_string=f'An event that performs {class_name.lower()}.',
            members=Stmt.new_decl_stmt(method_member),
        )

    class_names = [
        ('Add', 'int'), ('Subtract', 'int'), ('Multiply', 'int'),
        ('Divide', 'float'), ('Modulus', 'int'), ('Exponentiate', 'float'),
    ]

    # Build event sections chained via .next
    first_event_section = None
    prev_section = None
    for class_name, return_kind in class_names:
        cls = make_operator_class(class_name, return_kind)
        section = Stmt.new_artifact_stmt(
            section_header=Decl.new_artifact_decl(f'event: {class_name.lower()}', '**'),
            section_body=Stmt.new_decl_stmt(cls),
        )
        if first_event_section is None:
            first_event_section = section
        if prev_section is not None:
            prev_section.set_next(section)
        prev_section = section

    events_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('events', '***'),
        section_body=first_event_section,
    )
    imports_section.set_next(events_section)

    return Decl.new_module_decl(name='pass_multiple_operator_events', code=imports_section)


# *** tests

# ** test: build_imports_only
def test_build_imports_only(imports_only_ast: Decl):
    '''Build symbol table for imports-only module. Expect 4 imports, no class scopes.'''

    builder = SymbolTableBuilder()
    result = builder.build(imports_only_ast)

    assert result['module_name'] == 'pass_imports_only'
    assert 'module' in builder.scopes

    module_scope = builder.scopes['module']
    assert module_scope.has_symbol('Any')
    assert module_scope.has_symbol('DomainEvent')
    assert module_scope.has_symbol('a')
    assert module_scope.has_symbol('ErrorService')
    assert module_scope.get_symbol('Any').source_module == 'typing'
    assert module_scope.get_symbol('DomainEvent').source_module == '.settings'
    assert module_scope.get_symbol('ErrorService').source_module == '..interfaces'

    # No class scopes.
    assert len(builder.scopes) == 1


# ** test: build_minimal_event
def test_build_minimal_event(minimal_event_ast: Decl):
    '''Build symbol table for minimal event. Expect module + Ping class + execute method scopes.'''

    builder = SymbolTableBuilder()
    builder.build(minimal_event_ast)

    assert 'module' in builder.scopes
    assert 'module.Ping' in builder.scopes
    assert 'module.Ping.execute' in builder.scopes

    # Module has DomainEvent import and Ping class.
    module = builder.scopes['module']
    assert module.has_symbol('DomainEvent')
    assert module.has_symbol('Ping')
    assert module.get_symbol('Ping').kind == SymbolKind.CLASS_DEF

    # Ping has execute method.
    ping = builder.scopes['module.Ping']
    assert ping.has_symbol('execute')
    assert ping.get_symbol('execute').kind == SymbolKind.METHOD

    # execute has self and kwargs params.
    execute = builder.scopes['module.Ping.execute']
    assert execute.has_symbol('self')
    assert execute.has_symbol('kwargs')


# ** test: build_minimal_injection_event
def test_build_minimal_injection_event(injection_event_ast: Decl):
    '''Build symbol table for injection event. Expect pong attribute, __init__ and execute methods.'''

    builder = SymbolTableBuilder()
    builder.build(injection_event_ast)

    assert 'module.Ping' in builder.scopes
    assert 'module.Ping.__init__' in builder.scopes
    assert 'module.Ping.execute' in builder.scopes

    # Ping class has pong attribute plus two methods.
    ping = builder.scopes['module.Ping']
    assert ping.has_symbol('pong')
    assert ping.get_symbol('pong').kind == SymbolKind.ATTRIBUTE
    assert ping.has_symbol('__init__')
    assert ping.has_symbol('execute')

    # __init__ has self and pong params.
    init_scope = builder.scopes['module.Ping.__init__']
    assert init_scope.has_symbol('self')
    assert init_scope.has_symbol('pong')
    assert init_scope.get_symbol('pong').kind == SymbolKind.PARAMETER
    assert init_scope.get_symbol('pong').type_annotation == 'str'


# ** test: build_multiple_operator_events
def test_build_multiple_operator_events(multi_operator_ast: Decl):
    '''Build symbol table for multi-operator module. Expect 6 class scopes with execute methods.'''

    builder = SymbolTableBuilder()
    builder.build(multi_operator_ast)

    # Module has DomainEvent import + 6 classes.
    module = builder.scopes['module']
    assert module.has_symbol('DomainEvent')

    class_names = ['Add', 'Subtract', 'Multiply', 'Divide', 'Modulus', 'Exponentiate']
    for cls_name in class_names:
        assert module.has_symbol(cls_name), f'{cls_name} not in module scope'
        class_path = f'module.{cls_name}'
        assert class_path in builder.scopes, f'{class_path} scope not found'
        method_path = f'{class_path}.execute'
        assert method_path in builder.scopes, f'{method_path} scope not found'

        # Each execute has self, a, b params.
        method_scope = builder.scopes[method_path]
        assert method_scope.has_symbol('self')
        assert method_scope.has_symbol('a')
        assert method_scope.has_symbol('b')

    # 1 module + 6 classes + 6 methods = 13 scopes.
    assert len(builder.scopes) == 13


# ** test: resolve_minimal_event
def test_resolve_minimal_event(minimal_event_ast: Decl):
    '''Resolve names in minimal event. DomainEvent base class should resolve to module import.'''

    builder = SymbolTableBuilder()
    builder.build(minimal_event_ast)

    resolver = NameResolver(builder.scopes)
    result = resolver.resolve(minimal_event_ast)

    # DomainEvent (base class of Ping) should resolve.
    resolved_names = [r.name for r in result.resolved]
    assert 'DomainEvent' in resolved_names

    # No unresolved names expected.
    assert len(result.unresolved) == 0


# ** test: resolve_injection_event
def test_resolve_injection_event(injection_event_ast: Decl):
    '''Resolve names in injection event. self.pong should resolve to Ping class scope.'''

    builder = SymbolTableBuilder()
    builder.build(injection_event_ast)

    resolver = NameResolver(builder.scopes)
    result = resolver.resolve(injection_event_ast)

    # DomainEvent base class should resolve.
    resolved_names = [r.name for r in result.resolved]
    assert 'DomainEvent' in resolved_names

    # No unresolved names expected.
    assert len(result.unresolved) == 0


# ** test: resolve_multiple_operators
def test_resolve_multiple_operators(multi_operator_ast: Decl):
    '''Resolve names in multi-operator module. All base class refs should resolve.'''

    builder = SymbolTableBuilder()
    builder.build(multi_operator_ast)

    resolver = NameResolver(builder.scopes)
    result = resolver.resolve(multi_operator_ast)

    # 6 base class references to DomainEvent should all resolve.
    domain_event_refs = [r for r in result.resolved if r.name == 'DomainEvent']
    assert len(domain_event_refs) == 6

    assert len(result.unresolved) == 0


# ** test: self_is_skipped
def test_self_is_skipped(minimal_event_ast: Decl):
    '''Verify that bare self references are not recorded as resolved or unresolved.'''

    builder = SymbolTableBuilder()
    builder.build(minimal_event_ast)

    resolver = NameResolver(builder.scopes)
    result = resolver.resolve(minimal_event_ast)

    # 'self' should not appear in resolved or unresolved.
    all_names = [r.name for r in result.resolved] + [u.name for u in result.unresolved]
    assert 'self' not in all_names


# ** test: comments_skipped
def test_comments_skipped(minimal_event_ast: Decl):
    '''Verify that comment text is not treated as a name reference.'''

    builder = SymbolTableBuilder()
    builder.build(minimal_event_ast)

    resolver = NameResolver(builder.scopes)
    result = resolver.resolve(minimal_event_ast)

    # No comment text should appear in resolved or unresolved.
    all_names = [r.name for r in result.resolved] + [u.name for u in result.unresolved]
    assert '# Return pong.' not in all_names


# ** test: type_check_valid_int_addition
def test_type_check_valid_int_addition(multi_operator_ast: Decl):
    '''Type check valid int + int operations. Should return no errors.'''

    builder = SymbolTableBuilder()
    builder.build(multi_operator_ast)

    checker = TypeChecker(builder.scopes)
    errors = checker.check(multi_operator_ast)
    assert len(errors) == 0


# ** test: type_check_incompatible_binary_op
def test_type_check_incompatible_binary_op():
    '''Type check int + str should raise TYPE_MISMATCH_OPERATION.'''

    # Build a minimal module with a method that returns int_val + str_val.
    import_de = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('.settings'),
        import_expr=Expr.new_name_expr('DomainEvent'),
    )
    app_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('app', '**'),
        section_body=import_de,
    )
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=app_group,
    )

    # Method: execute(self, **kwargs) -> int with return 1 + 'hello'
    kwargs_param = ParamList.new_kwargs_param()
    self_param = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)
    self_param.set_next(kwargs_param)

    bad_add = Expr(kind='add', left=Expr(kind='int_val', value='1'), right=Expr(kind='str_val', value='hello'))
    return_stmt = Stmt.new_return_stmt(return_expr=bad_add)
    snippet = Stmt.new_snippet_stmt(code=return_stmt)

    execute_decl = Decl.new_func_decl(
        name='execute',
        type=Type.new_func_type(params=self_param, return_type=Type.new(kind='int')),
        body=snippet,
    )
    method_member = Decl.new_member_decl(
        name='method',
        member_body=Stmt.new_decl_stmt(execute_decl),
    )
    bad_class = Decl.new_class_decl(
        name='BadAdd',
        subclasses=Type.new_class_type(name='DomainEvent'),
        doc_string=None, members=Stmt.new_decl_stmt(method_member),
    )
    event_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('event: bad_add', '**'),
        section_body=Stmt.new_decl_stmt(bad_class),
    )
    events_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('events', '***'),
        section_body=event_section,
    )
    imports_section.set_next(events_section)

    module = Decl.new_module_decl(name='fail_type_check', code=imports_section)

    builder = SymbolTableBuilder()
    builder.build(module)

    checker = TypeChecker(builder.scopes)
    errors = checker.check(module)
    assert len(errors) == 1
    assert errors[0]['error_code'] == 'TYPE_MISMATCH_OPERATION'


# ** test: type_check_assignment_mismatch
def test_type_check_assignment_mismatch():
    '''Type check assigning str to a variable declared as int should raise TYPE_MISMATCH_ASSIGNMENT.'''

    # Build a minimal module with __init__ that assigns a str literal to a typed int param.
    import_de = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('.settings'),
        import_expr=Expr.new_name_expr('DomainEvent'),
    )
    app_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('app', '**'),
        section_body=import_de,
    )
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=app_group,
    )

    # Attribute: count: int
    count_attr = Decl.new_attr_decl(name='count', types=Type.new(kind='int'))
    attr_member = Decl.new_member_decl(
        name='attribute',
        member_body=Stmt.new_decl_stmt(count_attr),
    )

    # __init__(self, count: int) with self.count = 'bad_string'
    count_param = ParamList.new(name='count', type=Type.new(kind='int'), required=True)
    self_param = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)
    self_param.set_next(count_param)

    assign_stmt = Stmt(
        kind='expr',
        expr=Expr(kind='assign', left=Expr.new_name_expr('self.count'), right=Expr(kind='str_val', value='bad')),
    )
    init_snippet = Stmt.new_snippet_stmt(code=assign_stmt)

    init_decl = Decl.new_func_decl(
        name='__init__',
        type=Type.new_func_type(params=self_param, return_type=Type.new_null_type()),
        body=init_snippet,
    )
    init_member = Decl.new_member_decl(
        name='init',
        member_body=Stmt.new_decl_stmt(init_decl),
    )

    attr_member.next = init_member

    bad_class = Decl.new_class_decl(
        name='BadAssign',
        subclasses=Type.new_class_type(name='DomainEvent'),
        doc_string=None, members=Stmt.new_decl_stmt(attr_member),
    )
    event_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('event: bad_assign', '**'),
        section_body=Stmt.new_decl_stmt(bad_class),
    )
    events_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('events', '***'),
        section_body=event_section,
    )
    imports_section.set_next(events_section)

    module = Decl.new_module_decl(name='fail_type_assign', code=imports_section)

    builder = SymbolTableBuilder()
    builder.build(module)

    checker = TypeChecker(builder.scopes)
    errors = checker.check(module)
    assert len(errors) == 1
    assert errors[0]['error_code'] == 'TYPE_MISMATCH_ASSIGNMENT'


# ** test: type_check_str_concat_valid
def test_type_check_str_concat_valid():
    '''Type check str + str concatenation should pass without error.'''

    # Build a module with a method that returns str_val + str_val.
    import_de = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('.settings'),
        import_expr=Expr.new_name_expr('DomainEvent'),
    )
    app_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('app', '**'),
        section_body=import_de,
    )
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=app_group,
    )

    kwargs_param = ParamList.new_kwargs_param()
    self_param = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)
    self_param.set_next(kwargs_param)

    str_concat = Expr(kind='add', left=Expr(kind='str_val', value='hello'), right=Expr(kind='str_val', value=' world'))
    return_stmt = Stmt.new_return_stmt(return_expr=str_concat)
    snippet = Stmt.new_snippet_stmt(code=return_stmt)

    execute_decl = Decl.new_func_decl(
        name='execute',
        type=Type.new_func_type(params=self_param, return_type=Type.new(kind='str')),
        body=snippet,
    )
    method_member = Decl.new_member_decl(
        name='method',
        member_body=Stmt.new_decl_stmt(execute_decl),
    )
    ok_class = Decl.new_class_decl(
        name='Concat',
        subclasses=Type.new_class_type(name='DomainEvent'),
        doc_string=None, members=Stmt.new_decl_stmt(method_member),
    )
    event_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('event: concat', '**'),
        section_body=Stmt.new_decl_stmt(ok_class),
    )
    events_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('events', '***'),
        section_body=event_section,
    )
    imports_section.set_next(events_section)

    module = Decl.new_module_decl(name='pass_str_concat', code=imports_section)

    builder = SymbolTableBuilder()
    builder.build(module)

    checker = TypeChecker(builder.scopes)
    errors = checker.check(module)
    assert len(errors) == 0


# ** test: type_check_int_to_float_widening
def test_type_check_int_to_float_widening():
    '''Assigning int to a float-typed attribute should be allowed (widening).'''

    import_de = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('.settings'),
        import_expr=Expr.new_name_expr('DomainEvent'),
    )
    app_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('app', '**'),
        section_body=import_de,
    )
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=app_group,
    )

    # Attribute: rate: float
    rate_attr = Decl.new_attr_decl(name='rate', types=Type.new(kind='float'))
    attr_member = Decl.new_member_decl(
        name='attribute',
        member_body=Stmt.new_decl_stmt(rate_attr),
    )

    # __init__(self, rate: float) with self.rate = 5 (int literal)
    rate_param = ParamList.new(name='rate', type=Type.new(kind='float'), required=True)
    self_param = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)
    self_param.set_next(rate_param)

    assign_stmt = Stmt(
        kind='expr',
        expr=Expr(kind='assign', left=Expr.new_name_expr('self.rate'), right=Expr(kind='int_val', value='5')),
    )
    init_snippet = Stmt.new_snippet_stmt(code=assign_stmt)

    init_decl = Decl.new_func_decl(
        name='__init__',
        type=Type.new_func_type(params=self_param, return_type=Type.new_null_type()),
        body=init_snippet,
    )
    init_member = Decl.new_member_decl(
        name='init',
        member_body=Stmt.new_decl_stmt(init_decl),
    )

    attr_member.next = init_member

    ok_class = Decl.new_class_decl(
        name='Widen',
        subclasses=Type.new_class_type(name='DomainEvent'),
        doc_string=None, members=Stmt.new_decl_stmt(attr_member),
    )
    event_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('event: widen', '**'),
        section_body=Stmt.new_decl_stmt(ok_class),
    )
    events_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('events', '***'),
        section_body=event_section,
    )
    imports_section.set_next(events_section)

    module = Decl.new_module_decl(name='pass_int_to_float', code=imports_section)

    builder = SymbolTableBuilder()
    builder.build(module)

    checker = TypeChecker(builder.scopes)
    errors = checker.check(module)
    assert len(errors) == 0


# ** test: type_check_str_subtraction_invalid
def test_type_check_str_subtraction_invalid():
    '''Type check str - str should raise TYPE_MISMATCH_OPERATION (subtraction not valid for strings).'''

    import_de = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('.settings'),
        import_expr=Expr.new_name_expr('DomainEvent'),
    )
    app_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('app', '**'),
        section_body=import_de,
    )
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=app_group,
    )

    kwargs_param = ParamList.new_kwargs_param()
    self_param = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)
    self_param.set_next(kwargs_param)

    bad_sub = Expr(kind='sub', left=Expr(kind='str_val', value='hello'), right=Expr(kind='str_val', value='world'))
    return_stmt = Stmt.new_return_stmt(return_expr=bad_sub)
    snippet = Stmt.new_snippet_stmt(code=return_stmt)

    execute_decl = Decl.new_func_decl(
        name='execute',
        type=Type.new_func_type(params=self_param, return_type=Type.new(kind='str')),
        body=snippet,
    )
    method_member = Decl.new_member_decl(
        name='method',
        member_body=Stmt.new_decl_stmt(execute_decl),
    )
    bad_class = Decl.new_class_decl(
        name='BadSub',
        subclasses=Type.new_class_type(name='DomainEvent'),
        doc_string=None, members=Stmt.new_decl_stmt(method_member),
    )
    event_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('event: bad_sub', '**'),
        section_body=Stmt.new_decl_stmt(bad_class),
    )
    events_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('events', '***'),
        section_body=event_section,
    )
    imports_section.set_next(events_section)

    module = Decl.new_module_decl(name='fail_str_sub', code=imports_section)

    builder = SymbolTableBuilder()
    builder.build(module)

    checker = TypeChecker(builder.scopes)
    errors = checker.check(module)
    assert len(errors) == 1
    assert errors[0]['error_code'] == 'TYPE_MISMATCH_OPERATION'


# ** test: artifact_valid_import_groups
def test_artifact_valid_import_groups(imports_only_ast: Decl):
    '''Valid import groups (core, app) should produce no artifact errors.'''

    builder = SymbolTableBuilder()
    builder.build(imports_only_ast)

    checker = TypeChecker(builder.scopes)
    errors = checker.check(imports_only_ast)

    # No artifact structural errors expected.
    artifact_errors = [e for e in errors if e['error_code'].startswith('INVALID_IMPORT')]
    assert len(artifact_errors) == 0


# ** test: artifact_invalid_import_group_name
def test_artifact_invalid_import_group_name():
    '''Import group with invalid name should produce INVALID_IMPORT_GROUP.'''

    # Build a module with an import group named 'infra_bad'.
    import_any = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('typing'),
        import_expr=Expr.new_name_expr('Any'),
    )
    bad_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('infra_bad', '**'),
        section_body=import_any,
    )
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=bad_group,
    )
    module = Decl.new_module_decl(name='fail_import_group', code=imports_section)

    builder = SymbolTableBuilder()
    builder.build(module)

    checker = TypeChecker(builder.scopes)
    errors = checker.check(module)

    import_errors = [e for e in errors if e['error_code'] == 'INVALID_IMPORT_GROUP']
    assert len(import_errors) == 1
    assert import_errors[0]['group_name'] == 'infra_bad'


# ** test: artifact_import_section_with_class_decl
def test_artifact_import_section_with_class_decl():
    '''Class declaration in import section should produce INVALID_IMPORT_CONTENT.'''

    # Build a module with a class inside the 'core' import section.
    bad_class = Decl.new_class_decl(
        name='BadClass',
        subclasses=None,
        doc_string=None,
        members=None,
    )
    bad_stmt = Stmt.new_decl_stmt(bad_class)
    core_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('core', '**'),
        section_body=bad_stmt,
    )
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=core_group,
    )
    module = Decl.new_module_decl(name='fail_import_content', code=imports_section)

    builder = SymbolTableBuilder()
    builder.build(module)

    checker = TypeChecker(builder.scopes)
    errors = checker.check(module)

    content_errors = [e for e in errors if e['error_code'] == 'INVALID_IMPORT_CONTENT']
    assert len(content_errors) == 1
    assert content_errors[0]['section_name'] == 'core'


# ** test: artifact_section_class_name_match
def test_artifact_section_class_name_match(minimal_event_ast: Decl):
    '''Correct snake-to-pascal matching (ping -> Ping) should produce no errors.'''

    builder = SymbolTableBuilder()
    builder.build(minimal_event_ast)

    checker = TypeChecker(builder.scopes)
    errors = checker.check(minimal_event_ast)

    mismatch_errors = [e for e in errors if e['error_code'] == 'ARTIFACT_CLASS_NAME_MISMATCH']
    assert len(mismatch_errors) == 0


# ** test: artifact_section_class_name_mismatch
def test_artifact_section_class_name_mismatch():
    '''Mismatched class name should produce ARTIFACT_CLASS_NAME_MISMATCH.'''

    # Build event: add_error section with class named 'WrongName' instead of 'AddError'.
    import_de = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('.settings'),
        import_expr=Expr.new_name_expr('DomainEvent'),
    )
    app_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('app', '**'),
        section_body=import_de,
    )
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=app_group,
    )

    kwargs_param = ParamList.new_kwargs_param()
    self_param = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)
    self_param.set_next(kwargs_param)

    execute_decl = Decl.new_func_decl(
        name='execute',
        type=Type.new_func_type(params=self_param, return_type=Type.new(kind='str')),
        body=None,
    )
    method_member = Decl.new_member_decl(
        name='method',
        member_body=Stmt.new_decl_stmt(execute_decl),
    )
    wrong_class = Decl.new_class_decl(
        name='WrongName',
        subclasses=Type.new_class_type(name='DomainEvent'),
        doc_string=None,
        members=Stmt.new_decl_stmt(method_member),
    )
    event_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('add_error', '** event'),
        section_body=Stmt.new_decl_stmt(wrong_class),
    )
    events_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('events', '***'),
        section_body=event_section,
    )
    imports_section.set_next(events_section)

    module = Decl.new_module_decl(name='fail_class_name', code=imports_section)

    builder = SymbolTableBuilder()
    builder.build(module)

    checker = TypeChecker(builder.scopes)
    errors = checker.check(module)

    mismatch_errors = [e for e in errors if e['error_code'] == 'ARTIFACT_CLASS_NAME_MISMATCH']
    assert len(mismatch_errors) == 1
    assert mismatch_errors[0]['expected_class'] == 'AddError'
    assert mismatch_errors[0]['actual_class'] == 'WrongName'


# ** test: artifact_attribute_member_with_func
def test_artifact_attribute_member_with_func():
    '''Attribute member containing a function decl should produce INVALID_ATTRIBUTE_MEMBER_TYPE.'''

    import_de = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('.settings'),
        import_expr=Expr.new_name_expr('DomainEvent'),
    )
    app_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('app', '**'),
        section_body=import_de,
    )
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=app_group,
    )

    # Attribute member wrapping a function instead of a variable.
    self_param = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)
    bad_func = Decl.new_func_decl(
        name='bad_attr',
        type=Type.new_func_type(params=self_param, return_type=Type.new_null_type()),
        body=None,
    )
    attr_member = Decl.new_member_decl(
        name='attribute',
        member_body=Stmt.new_decl_stmt(bad_func),
    )

    bad_class = Decl.new_class_decl(
        name='BadAttr',
        subclasses=Type.new_class_type(name='DomainEvent'),
        doc_string=None,
        members=Stmt.new_decl_stmt(attr_member),
    )
    event_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('bad_attr', '** event'),
        section_body=Stmt.new_decl_stmt(bad_class),
    )
    events_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('events', '***'),
        section_body=event_section,
    )
    imports_section.set_next(events_section)

    module = Decl.new_module_decl(name='fail_attr_type', code=imports_section)

    builder = SymbolTableBuilder()
    builder.build(module)

    checker = TypeChecker(builder.scopes)
    errors = checker.check(module)

    attr_errors = [e for e in errors if e['error_code'] == 'INVALID_ATTRIBUTE_MEMBER_TYPE']
    assert len(attr_errors) == 1
    assert attr_errors[0]['found_type'] == 'function'


# ** test: artifact_method_member_missing_self
def test_artifact_method_member_missing_self():
    '''Method without self as first param should produce METHOD_MISSING_SELF.'''

    import_de = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('.settings'),
        import_expr=Expr.new_name_expr('DomainEvent'),
    )
    app_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('app', '**'),
        section_body=import_de,
    )
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=app_group,
    )

    # Method with 'cls' instead of 'self'.
    cls_param = ParamList.new(name='cls', type=Type.new_unknown_type(), required=True)
    bad_method = Decl.new_func_decl(
        name='execute',
        type=Type.new_func_type(params=cls_param, return_type=Type.new(kind='str')),
        body=None,
    )
    method_member = Decl.new_member_decl(
        name='method',
        member_body=Stmt.new_decl_stmt(bad_method),
    )

    bad_class = Decl.new_class_decl(
        name='NoSelf',
        subclasses=Type.new_class_type(name='DomainEvent'),
        doc_string=None,
        members=Stmt.new_decl_stmt(method_member),
    )
    event_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('no_self', '** event'),
        section_body=Stmt.new_decl_stmt(bad_class),
    )
    events_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('events', '***'),
        section_body=event_section,
    )
    imports_section.set_next(events_section)

    module = Decl.new_module_decl(name='fail_no_self', code=imports_section)

    builder = SymbolTableBuilder()
    builder.build(module)

    checker = TypeChecker(builder.scopes)
    errors = checker.check(module)

    self_errors = [e for e in errors if e['error_code'] == 'METHOD_MISSING_SELF']
    assert len(self_errors) == 1
    assert self_errors[0]['method_name'] == 'execute'
    assert self_errors[0]['first_param'] == 'cls'


# ** test: artifact_method_member_not_func
def test_artifact_method_member_not_func():
    '''Method member containing an attribute decl should produce INVALID_METHOD_MEMBER_TYPE.'''

    import_de = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('.settings'),
        import_expr=Expr.new_name_expr('DomainEvent'),
    )
    app_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('app', '**'),
        section_body=import_de,
    )
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=app_group,
    )

    # Method member wrapping a variable instead of a function.
    bad_attr = Decl.new_attr_decl(name='execute', types=Type.new(kind='str'))
    method_member = Decl.new_member_decl(
        name='method',
        member_body=Stmt.new_decl_stmt(bad_attr),
    )

    bad_class = Decl.new_class_decl(
        name='BadMethod',
        subclasses=Type.new_class_type(name='DomainEvent'),
        doc_string=None,
        members=Stmt.new_decl_stmt(method_member),
    )
    event_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('bad_method', '** event'),
        section_body=Stmt.new_decl_stmt(bad_class),
    )
    events_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('events', '***'),
        section_body=event_section,
    )
    imports_section.set_next(events_section)

    module = Decl.new_module_decl(name='fail_method_type', code=imports_section)

    builder = SymbolTableBuilder()
    builder.build(module)

    checker = TypeChecker(builder.scopes)
    errors = checker.check(module)

    method_errors = [e for e in errors if e['error_code'] == 'INVALID_METHOD_MEMBER_TYPE']
    assert len(method_errors) == 1


# ** test: artifact_event_has_execute
def test_artifact_event_has_execute(minimal_event_ast: Decl):
    '''Valid event with execute method should produce no EVENT_MISSING_EXECUTE errors.'''

    builder = SymbolTableBuilder()
    builder.build(minimal_event_ast)

    checker = TypeChecker(builder.scopes)
    errors = checker.check(minimal_event_ast)

    execute_errors = [e for e in errors if e['error_code'] == 'EVENT_MISSING_EXECUTE']
    assert len(execute_errors) == 0


# ** test: artifact_event_missing_execute
def test_artifact_event_missing_execute():
    '''Event class without execute method should produce EVENT_MISSING_EXECUTE.'''

    import_de = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('.settings'),
        import_expr=Expr.new_name_expr('DomainEvent'),
    )
    app_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('app', '**'),
        section_body=import_de,
    )
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=app_group,
    )

    # Event class with only an attribute — no execute method.
    pong_attr = Decl.new_attr_decl(name='pong', types=Type.new(kind='str'))
    attr_member = Decl.new_member_decl(
        name='attribute',
        member_body=Stmt.new_decl_stmt(pong_attr),
    )

    no_exec_class = Decl.new_class_decl(
        name='Ping',
        subclasses=Type.new_class_type(name='DomainEvent'),
        doc_string=None,
        members=Stmt.new_decl_stmt(attr_member),
    )
    event_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('ping', '** event'),
        section_body=Stmt.new_decl_stmt(no_exec_class),
    )
    events_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('events', '***'),
        section_body=event_section,
    )
    imports_section.set_next(events_section)

    module = Decl.new_module_decl(name='fail_no_execute', code=imports_section)

    builder = SymbolTableBuilder()
    builder.build(module)

    checker = TypeChecker(builder.scopes)
    errors = checker.check(module)

    exec_errors = [e for e in errors if e['error_code'] == 'EVENT_MISSING_EXECUTE']
    assert len(exec_errors) == 1
    assert exec_errors[0]['event_name'] == 'ping'
    assert exec_errors[0]['class_name'] == 'Ping'


# ** test: artifact_snake_to_pascal_conversion
def test_artifact_snake_to_pascal_conversion():
    '''Verify snake_to_pascal static method correctness.'''

    assert TypeChecker.snake_to_pascal('ping') == 'Ping'
    assert TypeChecker.snake_to_pascal('add_error') == 'AddError'
    assert TypeChecker.snake_to_pascal('perform_lexical_analysis') == 'PerformLexicalAnalysis'
    assert TypeChecker.snake_to_pascal('a') == 'A'


# *** helpers — method/event AST builders for local-variable tests

def _assign_stmt(target_name: str, value_expr) -> Stmt:
    '''Build an `expr` statement representing `<target_name> = <value_expr>`.'''

    return Stmt(
        kind='expr',
        expr=Expr(
            kind='assign',
            left=Expr.new_name_expr(target_name),
            right=value_expr,
        ),
    )


def _binary_expr(kind: str, left, right) -> Expr:
    '''Build a binary operator expression node.'''

    return Expr(kind=kind, left=left, right=right)


def _build_event_with_method(
    class_name: str,
    method_name: str,
    params: ParamList,
    return_type: Type,
    body: Stmt,
    attributes: list = None,
) -> Decl:
    '''Wrap a method body inside a minimal event module so the symbol-table
    builder traverses through artifact -> class -> method.
    '''

    # Imports section.
    import_de = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('.settings'),
        import_expr=Expr.new_name_expr('DomainEvent'),
    )
    app_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('app', '**'),
        section_body=import_de,
    )
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=app_group,
    )

    # Method.
    method_decl = Decl.new_func_decl(
        name=method_name,
        type=Type.new_func_type(params=params, return_type=return_type),
        body=Stmt.new_snippet_stmt(code=body),
    )
    method_member = Decl.new_member_decl(
        name='method' if method_name != '__init__' else 'init',
        member_body=Stmt.new_decl_stmt(method_decl),
    )

    # Optional attribute members come before the method member.
    members_root = None
    for attr_decl in attributes or []:
        attr_member = Decl.new_member_decl(
            name='attribute',
            member_body=Stmt.new_decl_stmt(attr_decl),
        )
        if members_root is None:
            members_root = attr_member
        else:
            members_root.set_next(attr_member)
    if members_root is None:
        members_root = method_member
    else:
        members_root.set_next(method_member)

    cls_decl = Decl.new_class_decl(
        name=class_name,
        subclasses=Type.new_class_type(name='DomainEvent'),
        doc_string=None,
        members=Stmt.new_decl_stmt(members_root),
    )

    # Use the snake_case form of the class name as the section name to
    # satisfy the artifact/class-name concordance check (PascalCase <-> snake).
    section_name = ''.join(
        ('_' + c.lower()) if c.isupper() else c for c in class_name
    ).lstrip('_')
    event_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl(section_name, '** event'),
        section_body=Stmt.new_decl_stmt(cls_decl),
    )
    events_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('events', '***'),
        section_body=event_section,
    )
    imports_section.set_next(events_section)

    return Decl.new_module_decl(name=f'pass_{section_name}', code=imports_section)


# *** tests — local variables: data types and scopes

# ** test: locals_register_with_inferred_types
def test_locals_register_with_inferred_types():
    '''Method-local assignments register VARIABLE symbols with types inferred
    from int, float, str, and arithmetic right-hand sides.'''

    self_param = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)

    # i = 1
    assign_i = _assign_stmt('i', Expr(kind='int_val', value='1'))
    # x = 1.5
    assign_x = _assign_stmt('x', Expr(kind='num_val', value='1.5'))
    # name = 'hi'
    assign_name = _assign_stmt('name', Expr(kind='str_val', value="'hi'"))
    # total = i + 2
    assign_total = _assign_stmt(
        'total',
        _binary_expr('add', Expr.new_name_expr('i'), Expr(kind='int_val', value='2')),
    )

    body = assign_i
    body.set_next(assign_x)
    body.set_next(assign_name)
    body.set_next(assign_total)
    body.set_next(Stmt.new_return_stmt(return_expr=Expr.new_name_expr('total')))

    module = _build_event_with_method(
        class_name='Calc',
        method_name='execute',
        params=self_param,
        return_type=Type.new(kind='int'),
        body=body,
    )

    builder = SymbolTableBuilder()
    builder.build(module)

    method_scope = builder.scopes['module.Calc.execute']
    assert method_scope.has_symbol('i')
    assert method_scope.has_symbol('x')
    assert method_scope.has_symbol('name')
    assert method_scope.has_symbol('total')

    assert method_scope.get_symbol('i').type_annotation == 'int'
    assert method_scope.get_symbol('x').type_annotation == 'float'
    assert method_scope.get_symbol('name').type_annotation == 'str'
    assert method_scope.get_symbol('total').type_annotation == 'int'
    assert method_scope.get_symbol('i').kind == SymbolKind.VARIABLE

    # No structural errors in this passing case.
    assert builder.errors == []


# ** test: locals_isolated_per_method_scope
def test_locals_isolated_per_method_scope():
    '''A local variable defined in one method scope must not leak into a sibling
    method scope on the same class. Demonstrates variable definitions across
    scopes.'''

    self_param_a = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)
    self_param_b = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)

    body_a = _assign_stmt('counter', Expr(kind='int_val', value='1'))
    body_a.set_next(Stmt.new_return_stmt(return_expr=Expr.new_name_expr('counter')))

    body_b = _assign_stmt('label', Expr(kind='str_val', value="'hello'"))
    body_b.set_next(Stmt.new_return_stmt(return_expr=Expr.new_name_expr('label')))

    # Build a class with two method members manually.
    method_a = Decl.new_func_decl(
        name='compute',
        type=Type.new_func_type(params=self_param_a, return_type=Type.new(kind='int')),
        body=Stmt.new_snippet_stmt(code=body_a),
    )
    method_b = Decl.new_func_decl(
        name='execute',
        type=Type.new_func_type(params=self_param_b, return_type=Type.new(kind='str')),
        body=Stmt.new_snippet_stmt(code=body_b),
    )

    member_a = Decl.new_member_decl('method', member_body=Stmt.new_decl_stmt(method_a))
    member_b = Decl.new_member_decl('method', member_body=Stmt.new_decl_stmt(method_b))
    member_a.set_next(member_b)

    cls_decl = Decl.new_class_decl(
        name='Twin',
        subclasses=Type.new_class_type(name='DomainEvent'),
        doc_string=None,
        members=Stmt.new_decl_stmt(member_a),
    )

    import_de = Stmt.new_import_stmt_from(
        from_expr=Expr.new_name_expr('.settings'),
        import_expr=Expr.new_name_expr('DomainEvent'),
    )
    app_group = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('app', '**'),
        section_body=import_de,
    )
    imports_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('imports', '***'),
        section_body=app_group,
    )
    event_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('twin', '** event'),
        section_body=Stmt.new_decl_stmt(cls_decl),
    )
    events_section = Stmt.new_artifact_stmt(
        section_header=Decl.new_artifact_decl('events', '***'),
        section_body=event_section,
    )
    imports_section.set_next(events_section)

    module = Decl.new_module_decl(name='pass_twin', code=imports_section)

    builder = SymbolTableBuilder()
    builder.build(module)

    compute_scope = builder.scopes['module.Twin.compute']
    execute_scope = builder.scopes['module.Twin.execute']

    # Each local lives only in its own method scope.
    assert compute_scope.has_symbol('counter')
    assert not compute_scope.has_symbol('label')
    assert execute_scope.has_symbol('label')
    assert not execute_scope.has_symbol('counter')
    assert compute_scope.get_symbol('counter').type_annotation == 'int'
    assert execute_scope.get_symbol('label').type_annotation == 'str'


# ** test: expression_resolves_names_from_different_scopes
def test_expression_resolves_names_from_different_scopes():
    '''An expression that combines a parameter, a class attribute (via
    self.attr), and a local variable must resolve every name through the
    name resolver.'''

    self_param = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)
    a_param = ParamList.new(name='a', type=Type.new(kind='int'), required=True)
    self_param.set_next(a_param)

    base_attr = Decl.new_attr_decl(name='base', types=Type.new(kind='int'))

    # local = a + 1
    assign_local = _assign_stmt(
        'local',
        _binary_expr('add', Expr.new_name_expr('a'), Expr(kind='int_val', value='1')),
    )
    # return self.base + local
    return_stmt = Stmt.new_return_stmt(
        return_expr=_binary_expr(
            'add',
            Expr.new_name_expr('self.base'),
            Expr.new_name_expr('local'),
        ),
    )
    assign_local.set_next(return_stmt)

    module = _build_event_with_method(
        class_name='ScopeMix',
        method_name='execute',
        params=self_param,
        return_type=Type.new(kind='int'),
        body=assign_local,
        attributes=[base_attr],
    )

    builder = SymbolTableBuilder()
    builder.build(module)
    resolver = NameResolver(builder.scopes)
    resolution = resolver.resolve(module)

    resolved_names = {(r.name, r.resolved_to) for r in resolution.resolved}

    # Parameter `a` resolves inside the method scope.
    assert ('a', 'module.ScopeMix.execute') in resolved_names

    # `self.base` resolves to the class scope where the attribute lives.
    assert ('self.base', 'module.ScopeMix') in resolved_names

    # Local `local` resolves inside the method scope.
    assert ('local', 'module.ScopeMix.execute') in resolved_names

    # No unresolved references.
    assert resolution.unresolved == []


# ** test: arithmetic_assignment_validates_data_type
def test_arithmetic_assignment_validates_data_type():
    '''An int-typed local can be reassigned (after passing the duplicate
    guard) to another int-typed arithmetic expression without raising a
    TYPE_MISMATCH_ASSIGNMENT error from the type checker.'''

    self_param = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)
    a_param = ParamList.new(name='a', type=Type.new(kind='int'), required=True)
    b_param = ParamList.new(name='b', type=Type.new(kind='int'), required=True)
    self_param.set_next(a_param)
    self_param.set_next(b_param)

    # total = a + b
    assign_total = _assign_stmt(
        'total',
        _binary_expr('add', Expr.new_name_expr('a'), Expr.new_name_expr('b')),
    )
    return_stmt = Stmt.new_return_stmt(return_expr=Expr.new_name_expr('total'))
    assign_total.set_next(return_stmt)

    module = _build_event_with_method(
        class_name='Adder',
        method_name='execute',
        params=self_param,
        return_type=Type.new(kind='int'),
        body=assign_total,
    )

    builder = SymbolTableBuilder()
    builder.build(module)
    checker = TypeChecker(builder.scopes)
    errors = checker.check(module)

    assert builder.scopes['module.Adder.execute'].get_symbol('total').type_annotation == 'int'
    assert [e for e in errors if e['error_code'] == 'TYPE_MISMATCH_ASSIGNMENT'] == []
    assert [e for e in errors if e['error_code'] == 'TYPE_MISMATCH_OPERATION'] == []


# *** tests — semantic errors: undefined, duplicate, shadow, type mismatch

# ** test: undefined_variable_is_unresolved
def test_undefined_variable_is_unresolved():
    '''A reference to an unknown identifier is captured as an UnresolvedName
    by the name resolver — satisfies the "undefined variable" requirement.'''

    self_param = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)

    # return missing
    return_stmt = Stmt.new_return_stmt(return_expr=Expr.new_name_expr('missing'))
    body = return_stmt

    module = _build_event_with_method(
        class_name='LogResult',
        method_name='execute',
        params=self_param,
        return_type=Type.new(kind='str'),
        body=body,
    )

    builder = SymbolTableBuilder()
    builder.build(module)
    resolution = NameResolver(builder.scopes).resolve(module)

    unresolved = [u.name for u in resolution.unresolved]
    assert 'missing' in unresolved


# ** test: duplicate_variable_same_scope
def test_duplicate_variable_same_scope():
    '''Re-assigning the same local name within a single method scope emits
    DUPLICATE_VARIABLE_SAME_SCOPE.'''

    self_param = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)

    assign_one = _assign_stmt('total', Expr(kind='int_val', value='1'))
    assign_two = _assign_stmt('total', Expr(kind='int_val', value='2'))
    return_stmt = Stmt.new_return_stmt(return_expr=Expr.new_name_expr('total'))

    body = assign_one
    body.set_next(assign_two)
    body.set_next(return_stmt)

    module = _build_event_with_method(
        class_name='DupVar',
        method_name='execute',
        params=self_param,
        return_type=Type.new(kind='int'),
        body=body,
    )

    builder = SymbolTableBuilder()
    builder.build(module)

    dup_errors = [
        e for e in builder.errors
        if e['error_code'] == 'DUPLICATE_VARIABLE_SAME_SCOPE'
    ]
    assert len(dup_errors) == 1
    assert dup_errors[0]['variable_name'] == 'total'
    assert dup_errors[0]['scope_path'] == 'module.DupVar.execute'


# ** test: variable_shadows_outer_scope
def test_variable_shadows_outer_scope():
    '''A local variable that shadows a class attribute defined in the
    enclosing class scope emits VARIABLE_SHADOWS_OUTER_SCOPE.'''

    self_param = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)

    # Class attribute: count: int.
    count_attr = Decl.new_attr_decl(name='count', types=Type.new(kind='int'))

    # Method local that shadows the class attribute: count = 5.
    assign_local = _assign_stmt('count', Expr(kind='int_val', value='5'))
    return_stmt = Stmt.new_return_stmt(return_expr=Expr.new_name_expr('count'))
    body = assign_local
    body.set_next(return_stmt)

    module = _build_event_with_method(
        class_name='ShadowVar',
        method_name='execute',
        params=self_param,
        return_type=Type.new(kind='int'),
        body=body,
        attributes=[count_attr],
    )

    builder = SymbolTableBuilder()
    builder.build(module)

    shadow_errors = [
        e for e in builder.errors
        if e['error_code'] == 'VARIABLE_SHADOWS_OUTER_SCOPE'
    ]
    assert len(shadow_errors) == 1
    assert shadow_errors[0]['variable_name'] == 'count'
    assert shadow_errors[0]['outer_scope_path'] == 'module.ShadowVar'
    assert shadow_errors[0]['outer_kind'] == 'attribute'


# ** test: assignment_type_mismatch_between_variables
def test_assignment_type_mismatch_between_variables():
    '''Assigning a str-typed variable's value to an int-typed self.attribute
    must surface a TYPE_MISMATCH_ASSIGNMENT error — satisfies the
    "assigning one variable to another with different data types" requirement.'''

    self_param = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)

    count_attr = Decl.new_attr_decl(name='count', types=Type.new(kind='int'))

    # label = 'hello'
    assign_label = _assign_stmt('label', Expr(kind='str_val', value="'hello'"))

    # self.count = label
    assign_attr = Stmt(
        kind='expr',
        expr=Expr(
            kind='assign',
            left=Expr.new_name_expr('self.count'),
            right=Expr.new_name_expr('label'),
        ),
    )

    return_stmt = Stmt.new_return_stmt(return_expr=Expr(kind='int_val', value='0'))

    body = assign_label
    body.set_next(assign_attr)
    body.set_next(return_stmt)

    module = _build_event_with_method(
        class_name='AssignVar',
        method_name='execute',
        params=self_param,
        return_type=Type.new(kind='int'),
        body=body,
        attributes=[count_attr],
    )

    builder = SymbolTableBuilder()
    builder.build(module)
    checker = TypeChecker(builder.scopes)
    errors = checker.check(module)

    mismatches = [e for e in errors if e['error_code'] == 'TYPE_MISMATCH_ASSIGNMENT']
    assert len(mismatches) == 1
    assert mismatches[0]['expected_type'] == 'int'
    assert mismatches[0]['actual_type'] == 'str'


# ** test: expression_type_mismatch_between_variables
def test_expression_type_mismatch_between_variables():
    '''Adding an int local to a str local must surface
    TYPE_MISMATCH_OPERATION on the binary expression.'''

    self_param = ParamList.new(name='self', type=Type.new_unknown_type(), required=True)

    assign_n = _assign_stmt('n', Expr(kind='int_val', value='5'))
    assign_s = _assign_stmt('s', Expr(kind='str_val', value="'oops'"))
    bad_expr_stmt = Stmt(
        kind='expr',
        expr=_binary_expr('add', Expr.new_name_expr('n'), Expr.new_name_expr('s')),
    )
    return_stmt = Stmt.new_return_stmt(return_expr=Expr(kind='int_val', value='0'))

    body = assign_n
    body.set_next(assign_s)
    body.set_next(bad_expr_stmt)
    body.set_next(return_stmt)

    module = _build_event_with_method(
        class_name='ExprMix',
        method_name='execute',
        params=self_param,
        return_type=Type.new(kind='int'),
        body=body,
    )

    builder = SymbolTableBuilder()
    builder.build(module)
    checker = TypeChecker(builder.scopes)
    errors = checker.check(module)

    op_errors = [e for e in errors if e['error_code'] == 'TYPE_MISMATCH_OPERATION']
    assert len(op_errors) == 1
    assert op_errors[0]['operation'] == 'add'
    assert op_errors[0]['left_type'] == 'int'
    assert op_errors[0]['right_type'] == 'str'
