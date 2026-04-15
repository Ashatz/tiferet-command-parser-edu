"""Type Checking Utility"""

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
from ..domain.semantic import SymbolKind
from ..mappers.semantic import ScopeAggregate

# *** utils

# ** util: type_checker
class TypeChecker:
    """
    AST walker that performs rudimentary type checking against the symbol table.
    Collects all type errors as descriptive dicts rather than raising immediately.
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
    def add_error(self, error_code: str, message: str, expr: Expression = None, **kwargs) -> None:
        """
        Record a type error with descriptive context.

        :param error_code: The error classification code.
        :type error_code: str
        :param message: Human-readable error description.
        :type message: str
        :param expr: The expression node where the error was detected (for position info).
        :type expr: Expression
        :param kwargs: Additional context fields (scope_path, types, etc.).
        :type kwargs: dict
        """

        error = {
            'error_code': error_code,
            'message': message,
            'scope_path': self.current_scope.path,
            **kwargs,
        }

        # Include position info from the expression node if available.
        if expr:
            if expr.lineno is not None:
                error['lineno'] = expr.lineno
            if expr.col is not None:
                error['col'] = expr.col

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
        """Recurse into artifact body."""

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

        # Artifact member wrapper — unwrap.
        if type_kind == TypeKind.ARTIFACT and metadata.get('type') == 'ARTIFACT_MEMBER':
            self.handle_artifact_member(decl)
            return

        # Class declaration — enter class scope, walk body.
        if type_kind == TypeKind.CLASS:
            self.handle_class_decl(decl)
            return

        # Method declaration — enter method scope, walk body.
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
        Checks assignment type compatibility and binary operation types.

        :param stmt: The expr statement.
        :type stmt: Statement
        """

        expr = stmt.expr
        if not expr:
            return

        # Check binary operations for type compatibility.
        if expr.kind in self.ARITHMETIC_OPS:
            self.check_binary_op(expr)
            return

        # Check assignments for type compatibility.
        if expr.kind == ExprKind.ASSIGN:
            self.check_assignment(expr)
            return

    # * method: handle_return
    def handle_return(self, stmt: Statement) -> None:
        """Check expressions in return statements."""

        if stmt.expr and stmt.expr.kind in self.ARITHMETIC_OPS:
            self.check_binary_op(stmt.expr)

    # * method: check_assignment
    def check_assignment(self, expr: Expression) -> None:
        """
        Check that the right-hand side of an assignment is compatible
        with the declared type of the left-hand side.

        :param expr: The assignment expression.
        :type expr: Expression
        """

        left = expr.left
        right = expr.right
        if not left or not right:
            return

        # Determine the declared type of the target.
        target_type = self.lookup_type(left)
        if not target_type:
            return

        # Infer the type of the right-hand side.
        value_type = self.infer_type(right)
        if not value_type:
            return

        # Check compatibility.
        if not self.types_compatible(target_type, value_type):
            self.add_error(
                error_code='TYPE_MISMATCH_ASSIGNMENT',
                message=f'Cannot assign {value_type} to variable declared as {target_type}',
                expr=expr,
                expected_type=target_type,
                actual_type=value_type,
                target_name=left.name or '',
            )

    # * method: check_binary_op
    def check_binary_op(self, expr: Expression) -> None:
        """
        Check that operands of a binary operation have compatible types.

        :param expr: The binary operation expression.
        :type expr: Expression
        """

        left_type = self.infer_type(expr.left) if expr.left else None
        right_type = self.infer_type(expr.right) if expr.right else None

        # If either side is unknown, skip checking.
        if not left_type or not right_type:
            return

        # Allow numeric + numeric for all arithmetic ops.
        if left_type in self.NUMERIC_TYPES and right_type in self.NUMERIC_TYPES:
            return

        # Allow str + str (concatenation) for add only.
        if expr.kind == ExprKind.ADD and left_type == 'str' and right_type == 'str':
            return

        # Allow str * int or int * str (repetition) for multiply only.
        if expr.kind == ExprKind.MUL:
            if (left_type == 'str' and right_type == 'int') or (left_type == 'int' and right_type == 'str'):
                return

        # Otherwise, type mismatch.
        self.add_error(
            error_code='TYPE_MISMATCH_OPERATION',
            message=f'Unsupported operand types for {expr.kind.value}: {left_type} and {right_type}',
            expr=expr,
            operation=expr.kind.value,
            left_type=left_type,
            right_type=right_type,
        )

    # * method: infer_type
    def infer_type(self, expr: Expression) -> Optional[str]:
        """
        Infer the type of an expression from its kind, literal value,
        or symbol table lookup.

        :param expr: The expression to infer.
        :type expr: Expression
        :return: The inferred type string, or None if unknown.
        :rtype: Optional[str]
        """

        if not expr:
            return None

        kind = expr.kind

        # Literal types.
        if kind == ExprKind.INT_VAL:
            return 'int'
        if kind == ExprKind.NUM_VAL:
            return 'float'
        if kind == ExprKind.STR_VAL:
            return 'str'
        if kind == ExprKind.BOOL_VAL:
            return 'bool'

        # Name reference — look up in symbol table.
        if kind == ExprKind.NAME:
            return self.lookup_type(expr)

        # Binary operations — infer result type from operands.
        if kind in self.ARITHMETIC_OPS:
            left_type = self.infer_type(expr.left) if expr.left else None
            right_type = self.infer_type(expr.right) if expr.right else None

            # String concatenation.
            if kind == ExprKind.ADD and left_type == 'str' and right_type == 'str':
                return 'str'

            # String repetition.
            if kind == ExprKind.MUL:
                if (left_type == 'str' and right_type == 'int') or (left_type == 'int' and right_type == 'str'):
                    return 'str'

            # Numeric result: float if either operand is float, else int.
            if left_type in self.NUMERIC_TYPES and right_type in self.NUMERIC_TYPES:
                if left_type == 'float' or right_type == 'float':
                    return 'float'
                return 'int'

        return None

    # * method: lookup_type
    def lookup_type(self, expr: Expression) -> Optional[str]:
        """
        Look up the type annotation for a name expression from the symbol table.

        :param expr: A name expression.
        :type expr: Expression
        :return: The type annotation string, or None.
        :rtype: Optional[str]
        """

        name = expr.name or ''
        if not name:
            return None

        # Handle self.X — look up X in enclosing class scope.
        if name.startswith('self.'):
            attr_name = name[5:]
            for scope in reversed(self.scope_stack):
                if scope.kind == SymbolKind.CLASS_DEF:
                    symbol = scope.get_symbol(attr_name)
                    if symbol:
                        return symbol.type_annotation
                    return None
            return None

        # Walk scope chain from current to module.
        for scope in reversed(self.scope_stack):
            symbol = scope.get_symbol(name)
            if symbol:
                return symbol.type_annotation

        return None

    # * method: types_compatible
    def types_compatible(self, declared: str, actual: str) -> bool:
        """
        Check if an actual type is compatible with a declared type.
        Allows int → float widening.

        :param declared: The declared type annotation.
        :type declared: str
        :param actual: The inferred actual type.
        :type actual: str
        :return: True if compatible, False otherwise.
        :rtype: bool
        """

        # Exact match.
        if declared == actual:
            return True

        # Allow int assigned to float (widening).
        if declared == 'float' and actual == 'int':
            return True

        return False
