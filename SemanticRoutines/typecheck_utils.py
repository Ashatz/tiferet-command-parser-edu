"""Type Checking Utility"""

# *** imports

# ** core
from typing import Dict, List, Optional, Union

# ** app
from .ast_domain import (
    TypeKind,
    ExprKind,
    StatementKind,
    Declaration,
    Statement,
    Expression,
    ParamList,
)
from .semantic_domain import SymbolKind
from .semantic_mapper import ScopeAggregate

# *** utils

# ** util: type_checker
class TypeChecker:
    """
    AST walker that performs rudimentary type checking against the symbol table.
    Collects all type errors as descriptive dicts rather than raising immediately.

    Error codes generated (error message generation):
      1. INVALID_IMPORT_GROUP — import section name not in {core, infra, app}
      2. INVALID_IMPORT_CONTENT — non-import statement inside import section
      3. ARTIFACT_CLASS_NAME_MISMATCH — section snake_case name != class PascalCase name
      4. EVENT_MISSING_EXECUTE — event class lacks an execute method
      5. INVALID_ATTRIBUTE_MEMBER_TYPE — attribute member wraps a function/class instead of variable
      6. ATTRIBUTE_MEMBER_NAME_MISMATCH — attribute member name doesn't match inner decl
      7. INVALID_METHOD_MEMBER_TYPE — method member wraps non-function
      8. METHOD_MEMBER_NAME_MISMATCH — method member name doesn't match inner decl
      9. METHOD_MISSING_SELF — method's first param is not 'self'
     10. INVALID_METHOD_RETURN_TYPE — return type is not a valid TypeKind
     11. TYPE_MISMATCH_ASSIGNMENT — RHS type incompatible with declared LHS type
     12. TYPE_MISMATCH_OPERATION — binary operator applied to incompatible types
    """

    # * attribute: NUMERIC_TYPES
    NUMERIC_TYPES = {'int', 'float'}

    # * attribute: ARITHMETIC_OPS
    ARITHMETIC_OPS = {
        ExprKind.ADD, ExprKind.SUB, ExprKind.MUL,
        ExprKind.DIV, ExprKind.MOD, ExprKind.EXP,
    }

    # * attribute: VALID_IMPORT_GROUPS
    VALID_IMPORT_GROUPS = {'core', 'infra', 'app'}

    # * attribute: SECTION_KEYWORDS
    SECTION_KEYWORDS = {
        'event', 'model', 'context', 'repo', 'mapper',
        'util', 'interface', 'contract', 'command',
    }

    # * attribute: VALID_RETURN_KINDS
    VALID_RETURN_KINDS = {
        TypeKind.UNKNOWN, TypeKind.NONE, TypeKind.BOOL, TypeKind.STR,
        TypeKind.INT, TypeKind.FLOAT, TypeKind.LIST, TypeKind.DICT,
        TypeKind.CLASS,
    }

    # * attribute: scopes
    scopes: Dict[str, ScopeAggregate]

    # * attribute: scope_stack
    scope_stack: List[ScopeAggregate]

    # * attribute: errors
    errors: List[Dict]

    # * init
    def __init__(self, scopes: Dict[str, ScopeAggregate]):
        """
        Initialize the type checker with the scope registry.

        :param scopes: Flat dict of scope path to ScopeAggregate.
        :type scopes: Dict[str, ScopeAggregate]
        """

        self.scopes = scopes
        self.scope_stack = []
        self.errors = []

    # * method: check
    def check(self, module_decl: Declaration) -> List[Dict]:
        """
        Run type checking over the module AST.
        Returns a list of error dicts describing each type mismatch found.

        :param module_decl: The module root declaration.
        :type module_decl: Declaration
        :return: List of type error descriptors.
        :rtype: List[Dict]
        """

        # Reset state.
        self.scope_stack = []
        self.errors = []

        # Enter the module scope.
        module_scope = self.scopes.get('module')
        if not module_scope:
            return self.errors

        self.scope_stack.append(module_scope)

        # Walk the AST.
        if module_decl.code:
            self.walk_statements(module_decl.code)

        # Return the collected errors.
        return self.errors

    # * method: current_scope
    @property
    def current_scope(self) -> ScopeAggregate:
        """Return the current scope from the stack."""

        return self.scope_stack[-1]

    # * method: add_error
    def add_error(self, error_code: str, message: str, node: Union[Expression, Declaration, None] = None, **kwargs) -> None:
        """
        Record a type error with descriptive context.

        :param error_code: The error classification code.
        :type error_code: str
        :param message: Human-readable error description.
        :type message: str
        :param node: The AST node where the error was detected (for position info).
        :type node: Expression | Declaration | None
        :param kwargs: Additional context fields (scope_path, types, etc.).
        :type kwargs: dict
        """

        error = {
            'error_code': error_code,
            'message': message,
            'scope_path': self.current_scope.path if self.scope_stack else 'module',
            **kwargs,
        }

        # Include position info from the AST node if available.
        if node:
            lineno = getattr(node, 'lineno', None)
            col = getattr(node, 'col', None)
            if lineno is not None:
                error['lineno'] = lineno
            if col is not None:
                error['col'] = col

        self.errors.append(error)

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
        """
        Handle an artifact statement. Performs structural validation
        based on the artifact header, then recurses into the body.

        :param stmt: The artifact statement.
        :type stmt: Statement
        """

        header_decl = self.extract_artifact_header(stmt)

        if header_decl:
            metadata = header_decl.metadata or {}
            artifact_type = metadata.get('type', '')
            header_name = header_decl.name or ''

            # Check import group structure.
            if header_name == 'imports' and artifact_type == '***':
                self.check_import_group(stmt, header_decl)

            # Check section-class name concordance.
            if self.is_section_keyword(artifact_type):
                self.check_section_class_name(stmt, header_decl, header_name, artifact_type)

        # Recurse into artifact body.
        if stmt.body:
            self.walk_statements(stmt.body)

    # * method: handle_snippet
    def handle_snippet(self, stmt: Statement) -> None:
        """Recurse into snippet body."""

        if stmt.body:
            self.walk_statements(stmt.body)

    # * method: handle_decl
    def handle_decl(self, stmt: Statement) -> None:
        """
        Handle a declaration statement for type checking.

        :param stmt: The decl statement.
        :type stmt: Statement
        """

        decl = stmt.decl
        if not decl:
            return

        decl_type = decl.type
        type_kind = decl_type.kind if decl_type else None
        metadata = decl.metadata or {}

        # Artifact member wrapper — unwrap and validate.
        if type_kind == TypeKind.ARTIFACT and metadata.get('type') == 'ARTIFACT_MEMBER':
            self.check_artifact_member(decl)
            self.handle_artifact_member(decl)
            return

        # Class declaration.
        if type_kind == TypeKind.CLASS:
            self.handle_class_decl(decl)
            return

        # Method declaration.
        if type_kind == TypeKind.FUNC:
            self.handle_func_decl(decl)
            return

    # * method: handle_artifact_member
    def handle_artifact_member(self, decl: Declaration) -> None:
        """Unwrap artifact member and type-check inner declarations."""

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

    # * method: handle_class_decl
    def handle_class_decl(self, decl: Declaration) -> None:
        """Enter class scope and walk body."""

        name = decl.name
        class_path = f'{self.current_scope.path}.{name}'
        class_scope = self.scopes.get(class_path)

        if class_scope:
            self.scope_stack.append(class_scope)
            if decl.code:
                self.walk_statements(decl.code)
            self.scope_stack.pop()

    # * method: handle_func_decl
    def handle_func_decl(self, decl: Declaration) -> None:
        """Enter method scope and walk body."""

        name = decl.name
        method_path = f'{self.current_scope.path}.{name}'
        method_scope = self.scopes.get(method_path)

        if method_scope:
            self.scope_stack.append(method_scope)
            if decl.code:
                self.walk_statements(decl.code)
            self.scope_stack.pop()

    # * method: handle_expr_stmt
    def handle_expr_stmt(self, stmt: Statement) -> None:
        """
        Handle an expression statement for type checking.

        :param stmt: The expr statement.
        :type stmt: Statement
        """

        expr = stmt.expr
        if not expr:
            return

        if expr.kind in self.ARITHMETIC_OPS:
            self.check_binary_op(expr)
            return

        if expr.kind == ExprKind.ASSIGN:
            self.check_assignment(expr)
            return

    # * method: extract_artifact_header
    def extract_artifact_header(self, stmt: Statement) -> Optional[Declaration]:
        """Extract the artifact header declaration from an artifact statement."""

        return stmt.decl if stmt.decl else None

    # * method: is_section_keyword
    def is_section_keyword(self, artifact_type: str) -> bool:
        """Check if the artifact type string contains a section keyword."""

        for keyword in self.SECTION_KEYWORDS:
            if keyword in artifact_type:
                return True
        return False

    # * method: extract_section_keyword
    def extract_section_keyword(self, artifact_type: str) -> Optional[str]:
        """Extract the section keyword from the artifact type string."""

        for keyword in self.SECTION_KEYWORDS:
            if keyword in artifact_type:
                return keyword
        return None

    # * method: snake_to_pascal (static)
    @staticmethod
    def snake_to_pascal(snake: str) -> str:
        """Convert a snake_case string to PascalCase."""

        return ''.join(word.capitalize() for word in snake.split('_'))

    # * method: check_import_group
    def check_import_group(self, stmt: Statement, header_decl: Declaration) -> None:
        """Validate the structure of an imports group."""

        current = stmt.body
        while current:
            if current.kind == StatementKind.ARTIFACT:
                section_header = self.extract_artifact_header(current)
                if section_header:
                    section_name = section_header.name or ''

                    if section_name not in self.VALID_IMPORT_GROUPS:
                        self.add_error(
                            error_code='INVALID_IMPORT_GROUP',
                            message=f"Import group '{section_name}' must be one of: core, infra, app",
                            node=section_header,
                            group_name=section_name,
                        )

                    self.check_import_section_body(current.body, section_name, section_header)

            current = current.next

    # * method: check_import_section_body
    def check_import_section_body(self, body: Optional[Statement], section_name: str, section_header: Declaration) -> None:
        """Validate that an import section body contains only import statements."""

        current = body
        while current:
            if current.kind not in (StatementKind.IMPORT, StatementKind.IMPORT_FROM):
                self.add_error(
                    error_code='INVALID_IMPORT_CONTENT',
                    message=f"Import section '{section_name}' contains non-import statements",
                    node=section_header,
                    section_name=section_name,
                    found_kind=current.kind.value if current.kind else 'unknown',
                )
                break

            current = current.next

    # * method: check_section_class_name
    def check_section_class_name(self, stmt: Statement, header_decl: Declaration, header_name: str, artifact_type: str) -> None:
        """Validate section-class name concordance."""

        expected_class_name = self.snake_to_pascal(header_name)
        found_class_name = self.find_class_name_in_body(stmt.body)

        if found_class_name is None:
            return

        if found_class_name != expected_class_name:
            keyword = self.extract_section_keyword(artifact_type) or 'section'
            self.add_error(
                error_code='ARTIFACT_CLASS_NAME_MISMATCH',
                message=f"Section '{keyword}: {header_name}' expects class '{expected_class_name}' but found '{found_class_name}'",
                node=header_decl,
                expected_class=expected_class_name,
                actual_class=found_class_name,
            )

        # For event sections, verify execute method.
        keyword = self.extract_section_keyword(artifact_type)
        if keyword == 'event':
            class_decl = self.find_class_decl_in_body(stmt.body)
            if class_decl and not self.class_has_method(class_decl, 'execute'):
                self.add_error(
                    error_code='EVENT_MISSING_EXECUTE',
                    message=f"Event '{header_name}' class '{class_decl.name}' must declare an 'execute' method",
                    node=header_decl,
                    event_name=header_name,
                    class_name=class_decl.name,
                )

    # * method: find_class_decl_in_body
    def find_class_decl_in_body(self, body: Optional[Statement]) -> Optional[Declaration]:
        """Find the first class declaration in a statement chain."""

        current = body
        while current:
            if current.kind == StatementKind.DECL and current.decl:
                if current.decl.type and current.decl.type.kind == TypeKind.CLASS:
                    return current.decl
            current = current.next
        return None

    # * method: class_has_method
    def class_has_method(self, class_decl: Declaration, method_name: str) -> bool:
        """Check if a class declaration contains a method member with the given name."""

        if not class_decl.code:
            return False

        # Walk the class body statement chain and the chained Declaration
        # siblings within each statement. The parser packs all members
        # into a single decl statement plus a sibling-decl linked list.
        current = class_decl.code
        while current:
            if current.kind == StatementKind.DECL and current.decl:
                member_decl = current.decl
                while member_decl is not None:
                    metadata = member_decl.metadata or {}

                    if (member_decl.type
                            and member_decl.type.kind == TypeKind.ARTIFACT
                            and metadata.get('type') == 'ARTIFACT_MEMBER'
                            and member_decl.name in ('method', 'init')):
                        inner_decl = self.extract_inner_decl(member_decl)
                        if inner_decl and inner_decl.name == method_name:
                            return True

                    member_decl = member_decl.next

            current = current.next

        return False

    # * method: find_class_name_in_body
    def find_class_name_in_body(self, body: Optional[Statement]) -> Optional[str]:
        """Find the first class declaration name in a statement chain."""

        current = body
        while current:
            if current.kind == StatementKind.DECL and current.decl:
                if current.decl.type and current.decl.type.kind == TypeKind.CLASS:
                    return current.decl.name
            current = current.next
        return None

    # * method: check_artifact_member
    def check_artifact_member(self, decl: Declaration) -> None:
        """Validate an artifact member declaration."""

        member_kind = decl.name or ''

        if member_kind == 'attribute':
            self.check_attribute_member(decl)
        elif member_kind in ('method', 'init'):
            self.check_method_member(decl)

    # * method: check_attribute_member
    def check_attribute_member(self, decl: Declaration) -> None:
        """Validate attribute member: must be a variable, not func/class."""

        inner_decl = self.extract_inner_decl(decl)
        if not inner_decl:
            return

        inner_type = inner_decl.type
        inner_kind = inner_type.kind if inner_type else None
        expected_name = self.extract_member_name_from_metadata(decl)

        if inner_kind in (TypeKind.FUNC, TypeKind.CLASS):
            kind_label = 'function' if inner_kind == TypeKind.FUNC else 'class'
            self.add_error(
                error_code='INVALID_ATTRIBUTE_MEMBER_TYPE',
                message=f"Attribute member '{expected_name or inner_decl.name}' must be a variable declaration, not a {kind_label}",
                node=decl,
                attribute_name=expected_name or inner_decl.name,
                found_type=kind_label,
            )

        if expected_name and inner_decl.name != expected_name:
            self.add_error(
                error_code='ATTRIBUTE_MEMBER_NAME_MISMATCH',
                message=f"Attribute member expects '{expected_name}' but declaration is '{inner_decl.name}'",
                node=decl,
                expected_name=expected_name,
                actual_name=inner_decl.name,
            )

    # * method: check_method_member
    def check_method_member(self, decl: Declaration) -> None:
        """Validate method member: must be function, self first param, valid return type."""

        inner_decl = self.extract_inner_decl(decl)
        if not inner_decl:
            return

        inner_type = inner_decl.type
        inner_kind = inner_type.kind if inner_type else None
        member_kind = decl.name or ''
        expected_name = self.extract_member_name_from_metadata(decl)

        if inner_kind != TypeKind.FUNC:
            kind_label = inner_kind.value if inner_kind else 'unknown'
            self.add_error(
                error_code='INVALID_METHOD_MEMBER_TYPE',
                message=f"Method member '{expected_name or inner_decl.name}' must be a function declaration",
                node=decl,
                method_name=expected_name or inner_decl.name,
                found_type=kind_label,
            )
            return

        if member_kind == 'method' and expected_name and inner_decl.name != expected_name:
            self.add_error(
                error_code='METHOD_MEMBER_NAME_MISMATCH',
                message=f"Method member expects '{expected_name}' but declaration is '{inner_decl.name}'",
                node=decl,
                expected_name=expected_name,
                actual_name=inner_decl.name,
            )

        if inner_type and inner_type.params:
            if inner_type.params.name != 'self':
                self.add_error(
                    error_code='METHOD_MISSING_SELF',
                    message=f"Method '{inner_decl.name}' must have 'self' as first parameter",
                    node=inner_decl,
                    method_name=inner_decl.name,
                    first_param=inner_type.params.name,
                )
        else:
            self.add_error(
                error_code='METHOD_MISSING_SELF',
                message=f"Method '{inner_decl.name}' must have 'self' as first parameter",
                node=inner_decl,
                method_name=inner_decl.name,
            )

        if inner_type and inner_type.return_type:
            ret_kind = inner_type.return_type.kind
            if ret_kind and ret_kind not in self.VALID_RETURN_KINDS:
                self.add_error(
                    error_code='INVALID_METHOD_RETURN_TYPE',
                    message=f"Method '{inner_decl.name}' has invalid return type '{ret_kind.value}'",
                    node=inner_decl,
                    method_name=inner_decl.name,
                    return_type=ret_kind.value,
                )

    # * method: extract_inner_decl
    def extract_inner_decl(self, member_decl: Declaration) -> Optional[Declaration]:
        """Extract the inner declaration from an artifact member's code body."""

        if not member_decl.code:
            return None

        current = member_decl.code
        while current:
            if current.kind == StatementKind.DECL and current.decl:
                return current.decl
            if current.kind == StatementKind.EXPR:
                current = current.next
                continue
            current = current.next
        return None

    # * method: extract_member_name_from_metadata
    def extract_member_name_from_metadata(self, decl: Declaration) -> Optional[str]:
        """Extract the member identifier name from the artifact member token."""

        return None

    # * method: handle_return
    def handle_return(self, stmt: Statement) -> None:
        """Check expressions in return statements."""

        if stmt.expr and stmt.expr.kind in self.ARITHMETIC_OPS:
            self.check_binary_op(stmt.expr)

    # * method: check_assignment
    def check_assignment(self, expr: Expression) -> None:
        """Check assignment type compatibility."""

        left = expr.left
        right = expr.right
        if not left or not right:
            return

        target_type = self.lookup_type(left)
        if not target_type:
            return

        value_type = self.infer_type(right)
        if not value_type:
            return

        if not self.types_compatible(target_type, value_type):
            self.add_error(
                error_code='TYPE_MISMATCH_ASSIGNMENT',
                message=f'Cannot assign {value_type} to variable declared as {target_type}',
                node=expr,
                expected_type=target_type,
                actual_type=value_type,
                target_name=left.name or '',
            )

    # * method: check_binary_op
    def check_binary_op(self, expr: Expression) -> None:
        """Check that operands of a binary operation have compatible types."""

        left_type = self.infer_type(expr.left) if expr.left else None
        right_type = self.infer_type(expr.right) if expr.right else None

        if not left_type or not right_type:
            return

        if left_type in self.NUMERIC_TYPES and right_type in self.NUMERIC_TYPES:
            return

        if expr.kind == ExprKind.ADD and left_type == 'str' and right_type == 'str':
            return

        if expr.kind == ExprKind.MUL:
            if (left_type == 'str' and right_type == 'int') or (left_type == 'int' and right_type == 'str'):
                return

        self.add_error(
            error_code='TYPE_MISMATCH_OPERATION',
            message=f'Unsupported operand types for {expr.kind.value}: {left_type} and {right_type}',
            node=expr,
            operation=expr.kind.value,
            left_type=left_type,
            right_type=right_type,
        )

    # * method: infer_type
    def infer_type(self, expr: Expression) -> Optional[str]:
        """Infer the type of an expression from its kind, literal value, or symbol table."""

        if not expr:
            return None

        kind = expr.kind

        if kind == ExprKind.INT_VAL:
            return 'int'
        if kind == ExprKind.STR_VAL:
            return 'str'
        if kind == ExprKind.BOOL_VAL:
            return 'bool'

        if kind == ExprKind.NAME:
            return self.lookup_type(expr)

        if kind in self.ARITHMETIC_OPS:
            left_type = self.infer_type(expr.left) if expr.left else None
            right_type = self.infer_type(expr.right) if expr.right else None

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

    # * method: lookup_type
    def lookup_type(self, expr: Expression) -> Optional[str]:
        """Look up the type annotation for a name expression from the symbol table."""

        name = expr.name or ''
        if not name:
            return None

        if name.startswith('self.'):
            attr_name = name[5:]
            for scope in reversed(self.scope_stack):
                if scope.kind == SymbolKind.CLASS_DEF:
                    symbol = scope.get_symbol(attr_name)
                    if symbol:
                        return symbol.type_annotation
                    return None
            return None

        for scope in reversed(self.scope_stack):
            symbol = scope.get_symbol(name)
            if symbol:
                return symbol.type_annotation

        return None

    # * method: types_compatible
    def types_compatible(self, declared: str, actual: str) -> bool:
        """Check if an actual type is compatible with a declared type. Allows int -> float widening."""

        if declared == actual:
            return True
        if declared == 'float' and actual == 'int':
            return True
        return False
