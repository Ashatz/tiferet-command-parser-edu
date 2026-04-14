"""Tests for Semantic Analysis Builder and Name Resolver"""

# *** imports

# ** infra
import pytest

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
