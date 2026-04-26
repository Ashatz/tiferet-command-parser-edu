"""Semantic Analysis Builder and Name Resolver Utilities"""

# *** imports

# ** core
from typing import Dict, List, Optional

# ** app
from ..domain.ast import (
    TypeKind,
    ExprKind,
    StatementKind,
    Declaration,
    Statement,
    Expression,
    ParamList,
)
from ..domain.semantic import (
    SymbolKind,
    Symbol,
    ResolvedName,
    UnresolvedName,
    ResolutionResult,
)
from ..mappers.semantic import ScopeAggregate

# *** utils

# ** util: symbol_table_builder
class SymbolTableBuilder:
    """
    Single-pass AST walker that constructs a symbol table from a
    DeclarationAggregate (module root) produced by the parser.

    In addition to building scopes and registering symbols, the builder
    accumulates a list of structural semantic errors:
      - DUPLICATE_VARIABLE_SAME_SCOPE: a name re-assigned within the same scope.
      - VARIABLE_SHADOWS_OUTER_SCOPE: a method-local name shadows an outer
        class attribute, parameter, import, or variable.
    """

    # * attribute: NUMERIC_TYPES
    NUMERIC_TYPES = {'int', 'float'}

    # * attribute: ARITHMETIC_OPS
    ARITHMETIC_OPS = {
        ExprKind.ADD, ExprKind.SUB, ExprKind.MUL,
        ExprKind.DIV, ExprKind.MOD, ExprKind.EXP,
    }

    # * attribute: scopes
    scopes: Dict[str, ScopeAggregate]

    # * attribute: scope_stack
    scope_stack: List[ScopeAggregate]

    # * attribute: errors
    errors: List[Dict]

    # * init
    def __init__(self):
        """Initialize the builder with empty state."""

        self.scopes = {}
        self.scope_stack = []
        self.errors = []

    # * method: build
    def build(self, module_decl: Declaration) -> dict:
        """
        Build the symbol table from the module root declaration.

        :param module_decl: The module-level DeclarationAggregate from the parser.
        :type module_decl: Declaration
        :return: A dict with module_name, scopes, and root_scope_path.
        :rtype: dict
        """

        # Reset state for a fresh build.
        self.scopes = {}
        self.scope_stack = []
        self.errors = []

        # Create the module scope.
        module_name = module_decl.name or 'unknown'
        module_scope = ScopeAggregate.new_module_scope(module_name)
        self.register_scope(module_scope)
        self.scope_stack.append(module_scope)

        # Walk the module code (statement chain).
        if module_decl.code:
            self.walk_statements(module_decl.code)

        # Return the built symbol table.
        return {
            'module_name': module_name,
            'scopes': {
                path: scope.model_dump(exclude_none=True)
                for path, scope in self.scopes.items()
            },
            'root_scope_path': 'module',
        }

    # * method: current_scope
    @property
    def current_scope(self) -> ScopeAggregate:
        """Return the current scope from the stack."""

        return self.scope_stack[-1]

    # * method: register_scope
    def register_scope(self, scope: ScopeAggregate) -> None:
        """Register a scope in the flat registry."""

        self.scopes[scope.path] = scope

    # * method: push_scope
    def push_scope(self, scope: ScopeAggregate) -> None:
        """
        Push a new scope onto the stack and register it.

        :param scope: The scope to push.
        :type scope: ScopeAggregate
        """

        # Register the scope in the flat registry.
        self.register_scope(scope)

        # Add as child of the current scope.
        self.current_scope.add_child(scope.name, scope.path)

        # Push onto the stack.
        self.scope_stack.append(scope)

    # * method: pop_scope
    def pop_scope(self) -> None:
        """Pop the current scope from the stack."""

        self.scope_stack.pop()

    # * method: walk_statements
    def walk_statements(self, stmt: Statement) -> None:
        """
        Iterate a .next-chained statement list, dispatching by kind.

        :param stmt: The first Statement in the chain.
        :type stmt: Statement
        """

        current = stmt
        while current:
            kind = current.kind

            if kind == StatementKind.ARTIFACT:
                self.handle_artifact(current)
            elif kind == StatementKind.IMPORT_FROM:
                self.handle_import_from(current)
            elif kind == StatementKind.IMPORT:
                self.handle_import(current)
            elif kind == StatementKind.DECL:
                self.handle_decl(current)
            elif kind == StatementKind.EXPR:
                self.handle_expr_stmt(current)
            elif kind == StatementKind.SNIPPET:
                self.handle_snippet(current)
            # comment, return, block — no symbols to register

            current = current.next

    # * method: handle_artifact
    def handle_artifact(self, stmt: Statement) -> None:
        """
        Handle an artifact statement (transparent wrapper).
        Recurses into body.

        :param stmt: The artifact statement.
        :type stmt: Statement
        """

        if stmt.body:
            self.walk_statements(stmt.body)

    # * method: handle_import_from
    def handle_import_from(self, stmt: Statement) -> None:
        """
        Handle an import_from statement.
        Extracts module path and imported names, registers as import symbols.

        :param stmt: The import_from statement.
        :type stmt: Statement
        """

        # Extract the module path from init_expr.
        module_path = ''
        if stmt.init_expr and stmt.init_expr.name:
            module_path = stmt.init_expr.name

        # Collect imported names from the expr tree.
        names = self.collect_import_names(stmt.expr)

        # Register each imported name as a symbol.
        for name in names:
            symbol = Symbol(
                name=name,
                kind=SymbolKind.IMPORT,
                scope_path=self.current_scope.path,
                source_module=module_path,
            )
            self.current_scope.add_symbol(symbol)

    # * method: handle_import
    def handle_import(self, stmt: Statement) -> None:
        """
        Handle a bare import statement.

        :param stmt: The import statement.
        :type stmt: Statement
        """

        names = self.collect_import_names(stmt.expr)

        for name in names:
            symbol = Symbol(
                name=name,
                kind=SymbolKind.IMPORT,
                scope_path=self.current_scope.path,
            )
            self.current_scope.add_symbol(symbol)

    # * method: collect_import_names
    def collect_import_names(self, expr: Optional[Expression]) -> List[str]:
        """
        Recursively collect imported names from an import expression tree.
        Handles name, import_multi, and import_as expressions.

        :param expr: The expression.
        :type expr: Expression | None
        :return: List of imported name strings.
        :rtype: List[str]
        """

        if not expr:
            return []

        kind = expr.kind

        if kind == ExprKind.NAME:
            return [expr.name] if expr.name else []

        elif kind == ExprKind.IMPORT_MULTI:
            left_names = self.collect_import_names(expr.left)
            right_names = self.collect_import_names(expr.right)
            return left_names + right_names

        elif kind == ExprKind.IMPORT_AS:
            # Use the alias (right side) as the imported name.
            if expr.right and expr.right.name:
                return [expr.right.name]
            return []

        return []

    # * method: handle_decl
    def handle_decl(self, stmt: Statement) -> None:
        """
        Handle a declaration statement. Dispatches based on decl.type.kind.

        :param stmt: The decl statement.
        :type stmt: Statement
        """

        decl = stmt.decl
        if not decl:
            return

        decl_type = decl.type
        type_kind = decl_type.kind if decl_type else None
        metadata = decl.metadata or {}

        # Artifact member wrapper — unwrap and process inner declarations.
        if type_kind == TypeKind.ARTIFACT and metadata.get('type') == 'ARTIFACT_MEMBER':
            self.handle_artifact_member(decl)
            return

        # Class declaration.
        if type_kind == TypeKind.CLASS:
            self.handle_class_decl(decl)
            return

        # Function/method declaration.
        if type_kind == TypeKind.FUNC:
            self.handle_func_decl(decl)
            return

        # Attribute declaration (primitive or known type).
        if type_kind in (TypeKind.STR, TypeKind.INT, TypeKind.FLOAT, TypeKind.BOOL,
                         TypeKind.LIST, TypeKind.DICT, TypeKind.UNKNOWN, TypeKind.NONE):
            self.handle_attr_decl(decl, type_kind.value if type_kind else None)
            return

        # Class-typed attribute (type.kind == class but no code body).
        if type_kind == TypeKind.CLASS and not decl.code:
            type_name = decl_type.name if decl_type else None
            self.handle_attr_decl(decl, type_name)
            return

    # * method: handle_artifact_member
    def handle_artifact_member(self, decl: Declaration) -> None:
        """
        Unwrap an ARTIFACT_MEMBER declaration and process its inner code
        and chained .next declarations.

        :param decl: The artifact member declaration.
        :type decl: Declaration
        """

        # Process the inner code (the real declaration).
        if decl.code:
            self.walk_statements(decl.code)

        # Follow the .next chain of raw Declaration objects (not Statements).
        next_decl = decl.next
        while next_decl:
            next_type = next_decl.type
            next_kind = next_type.kind if next_type else None
            next_metadata = next_decl.metadata or {}

            if next_kind == TypeKind.ARTIFACT and next_metadata.get('type') == 'ARTIFACT_MEMBER':
                # Process this member's code.
                if next_decl.code:
                    self.walk_statements(next_decl.code)

                # Continue to next member.
                next_decl = next_decl.next
            else:
                break

    # * method: handle_class_decl
    def handle_class_decl(self, decl: Declaration) -> None:
        """
        Handle a class declaration: register symbol, push class scope,
        walk members, pop scope.

        :param decl: The class declaration.
        :type decl: Declaration
        """

        name = decl.name

        # Determine base class name.
        base_class = None
        if decl.type and decl.type.subtype:
            base_class = decl.type.subtype.name

        # Register the class symbol in the current scope.
        symbol = Symbol(
            name=name,
            kind=SymbolKind.CLASS_DEF,
            scope_path=self.current_scope.path,
            type_annotation=base_class,
        )
        self.current_scope.add_symbol(symbol)

        # Push a new class scope.
        class_scope = ScopeAggregate.new_class_scope(name, self.current_scope.path)
        self.push_scope(class_scope)

        # Walk class body (member statement chain).
        if decl.code:
            self.walk_statements(decl.code)

        # Pop the class scope.
        self.pop_scope()

    # * method: handle_func_decl
    def handle_func_decl(self, decl: Declaration) -> None:
        """
        Handle a function/method declaration: register symbol, push scope,
        register parameters, walk body, pop scope.

        :param decl: The function declaration.
        :type decl: Declaration
        """

        name = decl.name

        # Determine return type.
        return_type = None
        if decl.type and decl.type.return_type:
            return_type = decl.type.return_type.kind.value if decl.type.return_type.kind else None

        # Register the method symbol in the current scope.
        symbol = Symbol(
            name=name,
            kind=SymbolKind.METHOD,
            scope_path=self.current_scope.path,
            type_annotation=return_type,
        )
        self.current_scope.add_symbol(symbol)

        # Push a new method scope.
        method_scope = ScopeAggregate.new_method_scope(name, self.current_scope.path)
        self.push_scope(method_scope)

        # Register parameters from the params linked list.
        if decl.type and decl.type.params:
            self.register_params(decl.type.params)

        # Walk method body.
        if decl.code:
            self.walk_statements(decl.code)

        # Pop the method scope.
        self.pop_scope()

    # * method: register_params
    def register_params(self, param: ParamList) -> None:
        """
        Walk a ParamList linked list and register each parameter as a symbol.

        :param param: The first parameter in the linked list.
        :type param: ParamList
        """

        current = param
        while current:
            name = current.name
            type_annotation = current.type.kind.value if current.type and current.type.kind else None

            symbol = Symbol(
                name=name,
                kind=SymbolKind.PARAMETER,
                scope_path=self.current_scope.path,
                type_annotation=type_annotation,
            )
            self.current_scope.add_symbol(symbol)

            current = current.next

    # * method: handle_attr_decl
    def handle_attr_decl(self, decl: Declaration, type_annotation: Optional[str] = None) -> None:
        """
        Handle an attribute declaration: register as attribute symbol.

        :param decl: The attribute declaration.
        :type decl: Declaration
        :param type_annotation: The type annotation string.
        :type type_annotation: str | None
        """

        symbol = Symbol(
            name=decl.name,
            kind=SymbolKind.ATTRIBUTE,
            scope_path=self.current_scope.path,
            type_annotation=type_annotation,
        )
        self.current_scope.add_symbol(symbol)

    # * method: handle_expr_stmt
    def handle_expr_stmt(self, stmt: Statement) -> None:
        """
        Handle an expression statement. If it's a self.X = ... assignment,
        register X as an attribute in the enclosing class scope. Otherwise,
        if it's a bare assignment (e.g., `x = a + b`) inside a method scope,
        register x as a local VARIABLE symbol with an inferred type and
        emit duplicate / shadowing errors when applicable.

        :param stmt: The expr statement.
        :type stmt: Statement
        """

        expr = stmt.expr
        if not expr or expr.kind != ExprKind.ASSIGN:
            return

        left = expr.left
        if not left or not left.name:
            return

        left_name = left.name

        # Check for self.X pattern.
        if left_name.startswith('self.'):
            attr_name = left_name[5:]  # Strip 'self.'

            # Find the enclosing class scope.
            class_scope = self.find_enclosing_class_scope()
            if class_scope and not class_scope.has_symbol(attr_name):
                symbol = Symbol(
                    name=attr_name,
                    kind=SymbolKind.ATTRIBUTE,
                    scope_path=class_scope.path,
                )
                class_scope.add_symbol(symbol)
            return

        # Skip dotted assignments other than self.X (out of scope for local tracking).
        if '.' in left_name:
            return

        # Bare local assignment — only meaningful inside a method scope.
        if not self.scope_stack or self.current_scope.kind != SymbolKind.METHOD:
            return

        # Detect a duplicate definition in the same scope.
        if self.current_scope.has_symbol(left_name):
            self.add_error(
                error_code='DUPLICATE_VARIABLE_SAME_SCOPE',
                message=f"Variable '{left_name}' is already defined in scope '{self.current_scope.path}'",
                node=expr,
                variable_name=left_name,
            )
            return

        # Detect shadowing of an outer scope.
        outer = self.find_outer_symbol(left_name)
        if outer is not None:
            self.add_error(
                error_code='VARIABLE_SHADOWS_OUTER_SCOPE',
                message=(
                    f"Variable '{left_name}' shadows existing definition in outer "
                    f"scope '{outer.scope_path}'"
                ),
                node=expr,
                variable_name=left_name,
                outer_scope_path=outer.scope_path,
                outer_kind=outer.kind.value if outer.kind else None,
            )

        # Register the local variable with an inferred type annotation.
        type_annotation = self.infer_local_type(expr.right)
        symbol = Symbol(
            name=left_name,
            kind=SymbolKind.VARIABLE,
            scope_path=self.current_scope.path,
            type_annotation=type_annotation,
        )
        self.current_scope.add_symbol(symbol)

    # * method: handle_snippet
    def handle_snippet(self, stmt: Statement) -> None:
        """
        Handle a snippet statement (transparent wrapper). Recurses into body.

        :param stmt: The snippet statement.
        :type stmt: Statement
        """

        if stmt.body:
            self.walk_statements(stmt.body)

    # * method: find_enclosing_class_scope
    def find_enclosing_class_scope(self) -> Optional[ScopeAggregate]:
        """
        Walk the scope stack from top to bottom to find the nearest class scope.

        :return: The nearest enclosing class scope, or None.
        :rtype: Optional[ScopeAggregate]
        """

        for scope in reversed(self.scope_stack):
            if scope.kind == SymbolKind.CLASS_DEF:
                return scope
        return None

    # * method: find_outer_symbol
    def find_outer_symbol(self, name: str) -> Optional[Symbol]:
        """
        Look for a symbol with `name` in any scope strictly enclosing the
        current scope. Used for shadowing detection.

        :param name: The name to look up.
        :type name: str
        :return: The first matching Symbol from an outer scope, or None.
        :rtype: Optional[Symbol]
        """

        # Walk outer scopes (skip the current/innermost scope).
        for scope in reversed(self.scope_stack[:-1]):
            symbol = scope.get_symbol(name)
            if symbol:
                return symbol
        return None

    # * method: infer_local_type
    def infer_local_type(self, expr: Optional[Expression]) -> Optional[str]:
        """
        Infer the type annotation string for the right-hand side of a local
        assignment. Mirrors the simple inference rules used by the type
        checker so that locals participate in subsequent type compatibility
        checks.

        :param expr: The right-hand side expression.
        :type expr: Expression | None
        :return: A type annotation string, or None when unknown.
        :rtype: str | None
        """

        if not expr:
            return None

        kind = expr.kind

        # Direct literal mappings.
        if kind == ExprKind.INT_VAL:
            return 'int'
        if kind == ExprKind.NUM_VAL:
            value = expr.value or ''
            return 'float' if '.' in value else 'int'
        if kind == ExprKind.STR_VAL:
            return 'str'
        if kind == ExprKind.BOOL_VAL:
            return 'bool'

        # Name reference — resolve through the symbol table.
        if kind == ExprKind.NAME:
            return self.lookup_local_name_type(expr.name or '')

        # Arithmetic operation — propagate compatible operand types.
        if kind in self.ARITHMETIC_OPS:
            left_type = self.infer_local_type(expr.left)
            right_type = self.infer_local_type(expr.right)

            if kind == ExprKind.ADD and left_type == 'str' and right_type == 'str':
                return 'str'
            if kind == ExprKind.MUL:
                if (left_type == 'str' and right_type == 'int') or (left_type == 'int' and right_type == 'str'):
                    return 'str'
            if left_type in self.NUMERIC_TYPES and right_type in self.NUMERIC_TYPES:
                if left_type == 'float' or right_type == 'float':
                    return 'float'
                return 'int'

        return None

    # * method: lookup_local_name_type
    def lookup_local_name_type(self, name: str) -> Optional[str]:
        """
        Look up a name in the active scope chain to infer its type annotation.
        Used by `infer_local_type` for name references on the right-hand side
        of local assignments.

        :param name: The name to look up.
        :type name: str
        :return: The type annotation string, or None.
        :rtype: str | None
        """

        if not name:
            return None

        # Resolve self.X by checking the enclosing class scope.
        if name.startswith('self.'):
            attr_name = name[5:]
            class_scope = self.find_enclosing_class_scope()
            if class_scope:
                symbol = class_scope.get_symbol(attr_name)
                if symbol:
                    return symbol.type_annotation
            return None

        # Walk from the innermost scope outward.
        for scope in reversed(self.scope_stack):
            symbol = scope.get_symbol(name)
            if symbol:
                return symbol.type_annotation
        return None

    # * method: add_error
    def add_error(self, error_code: str, message: str, node: Optional[Expression] = None, **kwargs) -> None:
        """
        Record a structural semantic error discovered while building the
        symbol table.

        :param error_code: The error classification code.
        :type error_code: str
        :param message: Human-readable description.
        :type message: str
        :param node: Optional AST node carrying position info.
        :type node: Expression | None
        :param kwargs: Additional context fields.
        :type kwargs: dict
        """

        error = {
            'error_code': error_code,
            'message': message,
            'scope_path': self.current_scope.path if self.scope_stack else 'module',
            **kwargs,
        }

        # Capture position info from the AST node when available.
        if node is not None:
            lineno = getattr(node, 'lineno', None)
            col = getattr(node, 'col', None)
            if lineno is not None:
                error['lineno'] = lineno
            if col is not None:
                error['col'] = col

        self.errors.append(error)


# ** util: name_resolver
class NameResolver:
    """
    Second-pass AST walker that resolves name references against
    a pre-built symbol table (scope registry).
    """

    # * attribute: scopes
    scopes: Dict[str, ScopeAggregate]

    # * attribute: scope_stack
    scope_stack: List[ScopeAggregate]

    # * attribute: resolved
    resolved: List[ResolvedName]

    # * attribute: unresolved
    unresolved: List[UnresolvedName]

    # * init
    def __init__(self, scopes: Dict[str, ScopeAggregate]):
        """
        Initialize the resolver with the scope registry from the builder.

        :param scopes: Flat dict of scope path to ScopeAggregate.
        :type scopes: Dict[str, ScopeAggregate]
        """

        self.scopes = scopes
        self.scope_stack = []
        self.resolved = []
        self.unresolved = []

    # * method: resolve
    def resolve(self, module_decl: Declaration) -> ResolutionResult:
        """
        Resolve all name references in the AST.

        :param module_decl: The module root declaration.
        :type module_decl: Declaration
        :return: The resolution result with resolved and unresolved names.
        :rtype: ResolutionResult
        """

        # Reset state.
        self.scope_stack = []
        self.resolved = []
        self.unresolved = []

        # Enter the module scope.
        module_scope = self.scopes.get('module')
        if not module_scope:
            return ResolutionResult()

        self.scope_stack.append(module_scope)

        # Walk the AST.
        if module_decl.code:
            self.walk_statements(module_decl.code)

        return ResolutionResult(
            resolved=self.resolved,
            unresolved=self.unresolved,
        )

    # * method: current_scope
    @property
    def current_scope(self) -> ScopeAggregate:
        """Return the current scope from the stack."""

        return self.scope_stack[-1]

    # * method: walk_statements
    def walk_statements(self, stmt: Statement) -> None:
        """Iterate a .next-chained statement list, dispatching by kind."""

        current = stmt
        while current:
            kind = current.kind

            if kind == StatementKind.ARTIFACT:
                self.handle_artifact(current)
            elif kind == StatementKind.IMPORT_FROM:
                pass  # Imports are definitions, not references.
            elif kind == StatementKind.IMPORT:
                pass
            elif kind == StatementKind.DECL:
                self.handle_decl(current)
            elif kind == StatementKind.EXPR:
                self.handle_expr_stmt(current)
            elif kind == StatementKind.SNIPPET:
                self.handle_snippet(current)
            elif kind == StatementKind.RETURN:
                self.handle_return(current)

            current = current.next

    # * method: handle_artifact
    def handle_artifact(self, stmt: Statement) -> None:
        """Recurse into artifact body."""

        if stmt.body:
            self.walk_statements(stmt.body)

    # * method: handle_decl
    def handle_decl(self, stmt: Statement) -> None:
        """Handle a declaration statement for resolution."""

        decl = stmt.decl
        if not decl:
            return

        decl_type = decl.type
        type_kind = decl_type.kind if decl_type else None
        metadata = decl.metadata or {}

        # Artifact member wrapper — unwrap.
        if type_kind == TypeKind.ARTIFACT and metadata.get('type') == 'ARTIFACT_MEMBER':
            self.handle_artifact_member_resolve(decl)
            return

        # Class declaration — resolve base class name, enter class scope.
        if type_kind == TypeKind.CLASS:
            self.handle_class_decl_resolve(decl)
            return

        # Method declaration — enter method scope, walk body.
        if type_kind == TypeKind.FUNC:
            self.handle_func_decl_resolve(decl)
            return

    # * method: handle_artifact_member_resolve
    def handle_artifact_member_resolve(self, decl: Declaration) -> None:
        """Unwrap artifact member and resolve inner declarations."""

        if decl.code:
            self.walk_statements(decl.code)

        next_decl = decl.next
        while next_decl:
            next_type = next_decl.type
            next_kind = next_type.kind if next_type else None
            next_metadata = next_decl.metadata or {}

            if next_kind == TypeKind.ARTIFACT and next_metadata.get('type') == 'ARTIFACT_MEMBER':
                if next_decl.code:
                    self.walk_statements(next_decl.code)
                next_decl = next_decl.next
            else:
                break

    # * method: handle_class_decl_resolve
    def handle_class_decl_resolve(self, decl: Declaration) -> None:
        """Resolve base class reference and walk class body."""

        name = decl.name

        # Resolve the base class name.
        if decl.type and decl.type.subtype and decl.type.subtype.name:
            self.resolve_name(decl.type.subtype.name)

        # Enter class scope.
        class_path = f'{self.current_scope.path}.{name}'
        class_scope = self.scopes.get(class_path)
        if class_scope:
            self.scope_stack.append(class_scope)

            if decl.code:
                self.walk_statements(decl.code)

            self.scope_stack.pop()

    # * method: handle_func_decl_resolve
    def handle_func_decl_resolve(self, decl: Declaration) -> None:
        """Enter method scope and walk body for resolution."""

        name = decl.name

        # Enter method scope.
        method_path = f'{self.current_scope.path}.{name}'
        method_scope = self.scopes.get(method_path)
        if method_scope:
            self.scope_stack.append(method_scope)

            if decl.code:
                self.walk_statements(decl.code)

            self.scope_stack.pop()

    # * method: handle_expr_stmt
    def handle_expr_stmt(self, stmt: Statement) -> None:
        """Handle an expression statement for name resolution."""

        if stmt.expr:
            self.resolve_expr(stmt.expr)

    # * method: handle_snippet
    def handle_snippet(self, stmt: Statement) -> None:
        """Recurse into snippet body."""

        if stmt.body:
            self.walk_statements(stmt.body)

    # * method: handle_return
    def handle_return(self, stmt: Statement) -> None:
        """Resolve expressions in return statements."""

        if stmt.expr:
            self.resolve_expr(stmt.expr)

    # * method: resolve_expr
    def resolve_expr(self, expr: Expression) -> None:
        """
        Resolve name references within an expression tree.

        :param expr: The expression.
        :type expr: Expression
        """

        if not expr:
            return

        kind = expr.kind

        # Skip literals and comments.
        if kind in (ExprKind.STR_VAL, ExprKind.INT_VAL, ExprKind.BOOL_VAL, ExprKind.COMMENT):
            return

        # Name reference — resolve it.
        if kind == ExprKind.NAME:
            name = expr.name or ''

            # Skip self (implicit).
            if name == 'self':
                return

            # Handle self.X references.
            if name.startswith('self.'):
                attr_name = name[5:]
                self.resolve_self_attr(attr_name)
                return

            # Resolve regular name.
            if name:
                self.resolve_name(name)
            return

        # Assignment — resolve right side only (left is a definition).
        if kind == ExprKind.ASSIGN:
            if expr.right:
                self.resolve_expr(expr.right)
            return

        # Binary operations and other compound expressions — resolve both sides.
        if expr.left:
            self.resolve_expr(expr.left)
        if expr.right:
            self.resolve_expr(expr.right)

    # * method: resolve_name
    def resolve_name(self, name: str) -> None:
        """
        Look up a name by walking the scope chain from current to module.

        :param name: The name to resolve.
        :type name: str
        """

        # Walk from current scope up through parents.
        for scope in reversed(self.scope_stack):
            if scope.has_symbol(name):
                self.resolved.append(ResolvedName(
                    name=name,
                    scope_path=self.current_scope.path,
                    resolved_to=scope.path,
                ))
                return

        # Not found — record as unresolved.
        self.unresolved.append(UnresolvedName(
            name=name,
            scope_path=self.current_scope.path,
        ))

    # * method: resolve_self_attr
    def resolve_self_attr(self, attr_name: str) -> None:
        """
        Resolve a self.X reference by looking up X in the enclosing class scope.

        :param attr_name: The attribute name (after 'self.').
        :type attr_name: str
        """

        # Find the enclosing class scope.
        for scope in reversed(self.scope_stack):
            if scope.kind == SymbolKind.CLASS_DEF:
                if scope.has_symbol(attr_name):
                    self.resolved.append(ResolvedName(
                        name=f'self.{attr_name}',
                        scope_path=self.current_scope.path,
                        resolved_to=scope.path,
                    ))
                    return

                # Not found in class scope.
                self.unresolved.append(UnresolvedName(
                    name=f'self.{attr_name}',
                    scope_path=self.current_scope.path,
                ))
                return

        # No enclosing class scope found.
        self.unresolved.append(UnresolvedName(
            name=f'self.{attr_name}',
            scope_path=self.current_scope.path,
        ))
