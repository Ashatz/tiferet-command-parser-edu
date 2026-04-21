"""Optimizer Utilities: YAML Anchor/Alias, Constant Folding, Strength Reduction, and Return Analysis"""

# *** imports

# ** core
from typing import Any, Dict, List, Optional, Tuple

# ** app
from ..domain.ast import (
    Declaration,
    Expression,
    Statement,
    ExprKind,
    StatementKind,
    TypeKind,
)
from ..interfaces.optimizer import (
    OptimizerService,
    ASTOptimizerService,
    ASTStrengthReducerService,
    ReturnAnalyzerService,
)
from ..mappers.ast import ExpressionAggregate

# *** constants

# ** constant: unreachable_after_return_code
UNREACHABLE_AFTER_RETURN_CODE = 'UNREACHABLE_AFTER_RETURN'

# ** constant: unreachable_after_return_message
UNREACHABLE_AFTER_RETURN_MESSAGE = 'Statement is unreachable (follows a return statement)'

# *** utils

# ** util: yaml_anchor_optimizer
class YamlAnchorOptimizer(OptimizerService):
    '''
    Concrete optimizer that deduplicates repeated params and returns lists
    across events by sharing Python object references, enabling PyYAML to
    emit YAML anchors and aliases automatically.
    '''

    # * method: optimize
    def optimize(self, codegen: Dict[str, Any]) -> Dict[str, Any]:
        '''
        Optimize the codegen dict by replacing repeated params/returns lists
        with shared object references and collecting anchor declarations
        into a top-level vars section.

        :param codegen: The codegen output dict from TiferetGenerator.
        :type codegen: Dict[str, Any]
        :return: The optimized dict with vars and shared references.
        :rtype: Dict[str, Any]
        '''

        # Collect all params and returns lists with their locations.
        locations = self.collect_lists(codegen)

        # Build the vars list and share references for repeated structures.
        vars_list: List[Any] = []
        for fingerprint, entries in locations.items():
            kind, values = fingerprint

            # Only share lists that appear more than once.
            if len(entries) < 2:
                continue

            # Create one canonical list object shared by all locations.
            canonical = list(values)

            # Add the canonical object to vars for anchor declaration.
            vars_list.append(canonical)

            # Patch all locations to reference the canonical object.
            for parent, key in entries:
                parent[key] = canonical

        # Build the result with vars before evt_grp so anchors are declared first.
        if vars_list:
            result: Dict[str, Any] = {'vars': vars_list}
            result['evt_grp'] = codegen['evt_grp']
            return result

        # Return the original dict unchanged when no vars are needed.
        return codegen

    # * method: collect_lists
    def collect_lists(self, codegen: Dict[str, Any]) -> Dict[Tuple, List[Tuple[Dict, str]]]:
        '''
        Walk the codegen dict and collect all params and returns lists
        with their parent dict and key for later patching.

        :param codegen: The codegen output dict.
        :type codegen: Dict[str, Any]
        :return: Dict keyed by (kind, tuple(values)) to list of (parent_dict, key) locations.
        :rtype: Dict[Tuple, List[Tuple[Dict, str]]]
        '''

        # Initialize the collector.
        collected: Dict[Tuple, List[Tuple[Dict, str]]] = {}

        # Get events dict; return empty if no events.
        evt_grp = codegen.get('evt_grp', {})
        evts = evt_grp.get('evts', {})
        if not evts:
            return collected

        # Walk each event.
        for event_key, event in evts.items():

            # Collect from execute section.
            execute = event.get('execute', {})
            self.collect_from_callable(execute, collected)

            # Collect from methods section.
            methods = event.get('methods', {})
            for method_name, method in methods.items():
                self.collect_from_callable(method, collected)

        return collected

    # * method: collect_from_callable
    def collect_from_callable(self,
            callable_dict: Dict[str, Any],
            collected: Dict[Tuple, List[Tuple[Dict, str]]],
        ) -> None:
        '''
        Collect params and returns lists from an execute or method dict.

        :param callable_dict: The execute or method dict.
        :type callable_dict: Dict[str, Any]
        :param collected: The collector to append to.
        :type collected: Dict[Tuple, List[Tuple[Dict, str]]]
        '''

        # Collect params list.
        if 'params' in callable_dict:
            values = callable_dict['params']
            fingerprint = ('params', tuple(values))
            collected.setdefault(fingerprint, []).append((callable_dict, 'params'))

        # Collect returns list.
        if 'returns' in callable_dict:
            values = callable_dict['returns']
            fingerprint = ('returns', tuple(values))
            collected.setdefault(fingerprint, []).append((callable_dict, 'returns'))


# ** util: constant_folder
class ConstantFolder(ASTOptimizerService):
    '''
    Concrete AST optimizer that folds constant arithmetic expressions.

    Performs a post-order walk over the AST and replaces any binary
    arithmetic node whose both operands are numeric literals with a
    single literal node containing the compile-time result.  Variable
    references, calls, comparisons, and mixed constant/variable
    expressions are left untouched.

    Supported operators: add (+), sub (-), mul (*), div (/), mod (%), exp (**).
    Numeric literal kinds recognised as foldable: int_val, num_val.
    Division always produces num_val; all other all-integer operations
    produce int_val when the result is a whole number.
    '''

    # -- class-level constant sets -----------------------------------------

    ARITHMETIC_OPS = frozenset({
        ExprKind.ADD,
        ExprKind.SUB,
        ExprKind.MUL,
        ExprKind.DIV,
        ExprKind.MOD,
        ExprKind.EXP,
    })

    # Kinds that are unambiguously numeric.
    NUMERIC_KINDS = frozenset({
        ExprKind.INT_VAL,
        ExprKind.NUM_VAL,
    })

    # * method: is_numeric
    def is_numeric(self, expr: Expression) -> bool:
        '''
        Return True when *expr* holds a foldable numeric literal.

        Accepts INT_VAL and NUM_VAL nodes directly, and also STR_VAL nodes
        whose value string parses as a Python float — this covers integer
        tokens (e.g. ``3``, ``5``) that the parser stores as STR_VAL.

        :param expr: The expression node to test.
        :type expr: Expression
        :return: True if the node represents a numeric constant.
        :rtype: bool
        '''

        # Unambiguously numeric kinds always qualify.
        if expr.kind in self.NUMERIC_KINDS:
            return True

        # STR_VAL nodes qualify when their value parses as a number.
        if expr.kind == ExprKind.STR_VAL:
            try:
                float(expr.value)
                return True
            except (ValueError, TypeError):
                return False

        return False

    # * method: fold
    def fold(self, ast: Declaration) -> Declaration:
        '''
        Entry point: walk the full AST and fold constant sub-expressions.

        :param ast: The root DeclarationAggregate produced by the parser.
        :type ast: Declaration
        :return: The same root with constant sub-expressions replaced.
        :rtype: Declaration
        '''

        # Walk the declaration chain starting at the root.
        self.fold_declaration(ast)

        # Return the (mutated) root.
        return ast

    # * method: fold_declaration
    def fold_declaration(self, decl: Optional[Declaration]) -> None:
        '''
        Recursively fold constant expressions within a declaration chain.

        :param decl: A Declaration node, or None to stop recursion.
        :type decl: Declaration | None
        '''

        # Base case: nothing to fold.
        if decl is None:
            return

        # Fold constant expressions in the declaration value field.
        if decl.value is not None:
            decl.value = self.fold_expression(decl.value)

        # Recurse into the code block of the declaration.
        if decl.code is not None:
            self.fold_statement(decl.code)

        # Continue to the next declaration in the chain.
        if decl.next is not None:
            self.fold_declaration(decl.next)

    # * method: fold_statement
    def fold_statement(self, stmt: Optional[Statement]) -> None:
        '''
        Recursively fold constant expressions within a statement chain.

        :param stmt: A Statement node, or None to stop recursion.
        :type stmt: Statement | None
        '''

        # Base case: nothing to fold.
        if stmt is None:
            return

        # Fold expressions nested inside inline declarations.
        if stmt.decl is not None:
            self.fold_declaration(stmt.decl)

        # Fold the primary expression of the statement.
        if stmt.expr is not None:
            stmt.expr = self.fold_expression(stmt.expr)

        # Fold the initialisation expression (e.g. for-loop range).
        if stmt.init_expr is not None:
            stmt.init_expr = self.fold_expression(stmt.init_expr)

        # Recurse into statement bodies (if-else, for, while, snippet).
        if stmt.body is not None:
            self.fold_statement(stmt.body)

        # Recurse into the else branch.
        if stmt.else_body is not None:
            self.fold_statement(stmt.else_body)

        # Continue to the next statement in the chain.
        if stmt.next is not None:
            self.fold_statement(stmt.next)

    # * method: fold_expression
    def fold_expression(self, expr: Optional[Expression]) -> Optional[Expression]:
        '''
        Post-order fold of a single expression node.
        Recurses into children first, then attempts to fold the parent.

        :param expr: The expression to fold, or None.
        :type expr: Expression | None
        :return: The original node (possibly with mutated children) or a new
                 literal node when the entire sub-expression is constant.
        :rtype: Expression | None
        '''

        # Base case: nothing to fold.
        if expr is None:
            return None

        # Post-order: fold left child first, then right child.
        if expr.left is not None:
            expr.left = self.fold_expression(expr.left)

        if expr.right is not None:
            expr.right = self.fold_expression(expr.right)

        # Attempt to fold this node when both children are numeric literals.
        if (
            expr.kind in self.ARITHMETIC_OPS
            and expr.left is not None
            and expr.right is not None
            and self.is_numeric(expr.left)
            and self.is_numeric(expr.right)
        ):
            return self.evaluate(expr)

        # Return the node unchanged (children may have been folded above).
        return expr

    # * method: evaluate
    def evaluate(self, expr: Expression) -> ExpressionAggregate:
        '''
        Evaluate a constant binary arithmetic expression and return a new
        literal ExpressionAggregate with the computed value.

        :param expr: A binary arithmetic expression with two numeric literal children.
        :type expr: Expression
        :return: A new INT_VAL or NUM_VAL literal node.
        :rtype: ExpressionAggregate
        '''

        # Parse both operands as floats for uniform arithmetic.
        lval = float(expr.left.value)
        rval = float(expr.right.value)

        # Apply the operator.
        op = expr.kind
        if op == ExprKind.ADD:
            result = lval + rval
        elif op == ExprKind.SUB:
            result = lval - rval
        elif op == ExprKind.MUL:
            result = lval * rval
        elif op == ExprKind.DIV:
            result = lval / rval
        elif op == ExprKind.MOD:
            result = lval % rval
        else:  # ExprKind.EXP
            result = lval ** rval

        # Division always yields a float (NUM_VAL).  All other ops that
        # produce a whole-number result use STR_VAL to match parser convention;
        # INT_VAL and NUM_VAL source operands use their respective kinds.
        if op != ExprKind.DIV and isinstance(result, float) and result.is_integer():
            # Use STR_VAL for whole numbers when either operand was STR_VAL
            # (the common parser output), otherwise keep INT_VAL.
            result_kind = (
                ExprKind.INT_VAL
                if expr.left.kind in self.NUMERIC_KINDS and expr.right.kind in self.NUMERIC_KINDS
                else ExprKind.STR_VAL
            )
            return ExpressionAggregate(
                kind=result_kind,
                value=str(int(result)),
                lineno=expr.lineno,
                col=expr.col,
            )

        # Float results use NUM_VAL.
        return ExpressionAggregate(
            kind=ExprKind.NUM_VAL,
            value=str(result),
            lineno=expr.lineno,
            col=expr.col,
        )


# ** util: strength_reducer
class StrengthReducer(ASTStrengthReducerService):
    '''
    Concrete AST optimizer that rewrites a small set of expensive
    arithmetic operations into cheaper equivalents.

    Supported strength-reduction patterns:
      1. Multiplication by a positive integer power of two:
         ``x * 2**k``  -->  ``x << k`` (either operand may be the literal).
      2. Division by a positive integer power of two:
         ``x / 2**k``  -->  ``x >> k`` (only the right operand may be
         the literal; ``literal / x`` is left alone).
      3. Exponentiation by two:
         ``x ** 2``    -->  ``x * x`` (left operand is deep-copied so
         the two MUL children are distinct nodes).

    Anything that does not match one of the above patterns is left
    untouched. The pass is intended to run *after* constant folding
    so that simple literal arithmetic (e.g. ``2 * 4``) has already
    been reduced to a single literal operand.
    '''

    # -- class-level constant sets -----------------------------------------

    # Numeric literal kinds that may carry a power-of-two value.
    NUMERIC_KINDS = frozenset({
        ExprKind.INT_VAL,
        ExprKind.NUM_VAL,
    })

    # * method: is_power_of_two_literal
    def is_power_of_two_literal(self, expr: Optional[Expression]) -> Optional[int]:
        '''
        Return the base-2 logarithm of *expr* when it is a positive
        integer power-of-two literal, otherwise None.

        Accepts INT_VAL and NUM_VAL nodes directly, plus STR_VAL nodes
        whose value parses as a whole number (matching the parser
        convention that stores raw token values as STR_VAL).

        :param expr: The expression node to test.
        :type expr: Expression | None
        :return: The exponent k such that ``expr == 2**k``, or None.
        :rtype: int | None
        '''

        # Reject non-literal / non-numeric-string nodes outright.
        if expr is None:
            return None
        if expr.kind not in self.NUMERIC_KINDS and expr.kind != ExprKind.STR_VAL:
            return None
        if expr.value is None:
            return None

        # Convert to float first so we accept "8.0" as well as "8".
        try:
            as_float = float(expr.value)
        except (ValueError, TypeError):
            return None

        # Reject non-positive values and non-whole numbers.
        if as_float <= 0 or not as_float.is_integer():
            return None
        as_int = int(as_float)

        # Check for power-of-two via the classic bit trick.
        if as_int & (as_int - 1) != 0:
            return None

        # Return the exponent.
        return as_int.bit_length() - 1

    # * method: is_literal_two
    def is_literal_two(self, expr: Optional[Expression]) -> bool:
        '''
        Return True when *expr* is a numeric literal with value exactly 2.

        :param expr: The expression node to test.
        :type expr: Expression | None
        :return: True if the node represents the integer 2.
        :rtype: bool
        '''

        exponent = self.is_power_of_two_literal(expr)
        return exponent == 1

    # * method: deep_copy_expr
    def deep_copy_expr(self, expr: Expression) -> ExpressionAggregate:
        '''
        Produce a structural deep copy of *expr* as an
        ExpressionAggregate so the synthesized self-multiplication
        (``x * x``) has two distinct operand nodes.

        :param expr: The expression to clone.
        :type expr: Expression
        :return: A deep-copied ExpressionAggregate.
        :rtype: ExpressionAggregate
        '''

        # Recurse into each child; None children stay None.
        left_copy = self.deep_copy_expr(expr.left) if expr.left is not None else None
        right_copy = self.deep_copy_expr(expr.right) if expr.right is not None else None

        # Build a new aggregate mirroring the original node.
        return ExpressionAggregate(
            kind=expr.kind,
            value=expr.value,
            name=expr.name,
            left=left_copy,
            right=right_copy,
            lineno=expr.lineno,
            col=expr.col,
        )

    # * method: make_int_literal
    def make_int_literal(self,
            value: int,
            lineno: Optional[int],
            col: Optional[int],
        ) -> ExpressionAggregate:
        '''
        Build an INT_VAL literal node carrying *value* with the same
        source position as its enclosing expression.

        :param value: The integer value to store.
        :type value: int
        :param lineno: Source line number for the new node.
        :type lineno: int | None
        :param col: Source column for the new node.
        :type col: int | None
        :return: A new INT_VAL ExpressionAggregate.
        :rtype: ExpressionAggregate
        '''

        return ExpressionAggregate(
            kind=ExprKind.INT_VAL,
            value=str(value),
            lineno=lineno,
            col=col,
        )

    # * method: reduce
    def reduce(self, ast: Declaration) -> Declaration:
        '''
        Entry point: walk the full AST and rewrite matching
        arithmetic sub-expressions in place.

        :param ast: The root DeclarationAggregate produced by the parser.
        :type ast: Declaration
        :return: The same root with strength-reduced sub-expressions.
        :rtype: Declaration
        '''

        # Walk the declaration chain starting at the root.
        self.reduce_declaration(ast)

        # Return the (mutated) root.
        return ast

    # * method: reduce_declaration
    def reduce_declaration(self, decl: Optional[Declaration]) -> None:
        '''
        Recursively strength-reduce expressions within a declaration chain.

        :param decl: A Declaration node, or None to stop recursion.
        :type decl: Declaration | None
        '''

        # Base case: nothing to reduce.
        if decl is None:
            return

        # Reduce the declaration value field, if any.
        if decl.value is not None:
            decl.value = self.reduce_expression(decl.value)

        # Recurse into the declaration's code block.
        if decl.code is not None:
            self.reduce_statement(decl.code)

        # Continue to the next declaration in the chain.
        if decl.next is not None:
            self.reduce_declaration(decl.next)

    # * method: reduce_statement
    def reduce_statement(self, stmt: Optional[Statement]) -> None:
        '''
        Recursively strength-reduce expressions within a statement chain.

        :param stmt: A Statement node, or None to stop recursion.
        :type stmt: Statement | None
        '''

        # Base case: nothing to reduce.
        if stmt is None:
            return

        # Recurse into inline declarations.
        if stmt.decl is not None:
            self.reduce_declaration(stmt.decl)

        # Reduce the primary expression of the statement.
        if stmt.expr is not None:
            stmt.expr = self.reduce_expression(stmt.expr)

        # Reduce the initialisation expression (e.g. for-loop range).
        if stmt.init_expr is not None:
            stmt.init_expr = self.reduce_expression(stmt.init_expr)

        # Recurse into statement bodies (if-else, for, while, snippet).
        if stmt.body is not None:
            self.reduce_statement(stmt.body)

        # Recurse into the else branch.
        if stmt.else_body is not None:
            self.reduce_statement(stmt.else_body)

        # Continue to the next statement in the chain.
        if stmt.next is not None:
            self.reduce_statement(stmt.next)

    # * method: reduce_expression
    def reduce_expression(self, expr: Optional[Expression]) -> Optional[Expression]:
        '''
        Post-order strength reduction of a single expression node.
        Recurses into children first, then attempts to rewrite the
        parent node.

        :param expr: The expression to reduce, or None.
        :type expr: Expression | None
        :return: The original node (possibly with mutated children)
                 or a new node when the sub-expression was rewritten.
        :rtype: Expression | None
        '''

        # Base case: nothing to reduce.
        if expr is None:
            return None

        # Post-order: reduce children first.
        if expr.left is not None:
            expr.left = self.reduce_expression(expr.left)

        if expr.right is not None:
            expr.right = self.reduce_expression(expr.right)

        # Pattern 1: multiplication by a power of two -> left shift.
        if expr.kind == ExprKind.MUL:
            return self.try_reduce_mul(expr)

        # Pattern 2: division by a power of two -> right shift.
        if expr.kind == ExprKind.DIV:
            return self.try_reduce_div(expr)

        # Pattern 3: exponentiation by two -> self-multiplication.
        if expr.kind == ExprKind.EXP:
            return self.try_reduce_exp(expr)

        # No applicable pattern; return unchanged.
        return expr

    # * method: try_reduce_mul
    def try_reduce_mul(self, expr: Expression) -> Expression:
        '''
        Reduce ``x * 2**k`` or ``2**k * x`` to ``x << k``.

        :param expr: A MUL expression node with both children present.
        :type expr: Expression
        :return: A new SHL node when the pattern applies, otherwise *expr*.
        :rtype: Expression
        '''

        # Bail out if the tree is malformed.
        if expr.left is None or expr.right is None:
            return expr

        # Prefer the right operand as the literal (common canonical form).
        right_k = self.is_power_of_two_literal(expr.right)
        if right_k is not None and right_k >= 1:
            shift_amount = self.make_int_literal(right_k, expr.right.lineno, expr.right.col)
            return ExpressionAggregate(
                kind=ExprKind.SHL,
                value='<<',
                left=expr.left,
                right=shift_amount,
                lineno=expr.lineno,
                col=expr.col,
            )

        # Otherwise accept the literal on the left (multiplication is commutative).
        left_k = self.is_power_of_two_literal(expr.left)
        if left_k is not None and left_k >= 1:
            shift_amount = self.make_int_literal(left_k, expr.left.lineno, expr.left.col)
            return ExpressionAggregate(
                kind=ExprKind.SHL,
                value='<<',
                left=expr.right,
                right=shift_amount,
                lineno=expr.lineno,
                col=expr.col,
            )

        # No applicable literal; leave the MUL in place.
        return expr

    # * method: try_reduce_div
    def try_reduce_div(self, expr: Expression) -> Expression:
        '''
        Reduce ``x / 2**k`` to ``x >> k``. Division is not commutative,
        so only the divisor (right operand) is examined.

        :param expr: A DIV expression node with both children present.
        :type expr: Expression
        :return: A new SHR node when the pattern applies, otherwise *expr*.
        :rtype: Expression
        '''

        # Bail out if the tree is malformed.
        if expr.left is None or expr.right is None:
            return expr

        # Only the divisor can be replaced.
        k = self.is_power_of_two_literal(expr.right)
        if k is None or k < 1:
            return expr

        shift_amount = self.make_int_literal(k, expr.right.lineno, expr.right.col)
        return ExpressionAggregate(
            kind=ExprKind.SHR,
            value='>>',
            left=expr.left,
            right=shift_amount,
            lineno=expr.lineno,
            col=expr.col,
        )

    # * method: try_reduce_exp
    def try_reduce_exp(self, expr: Expression) -> Expression:
        '''
        Reduce ``x ** 2`` to ``x * x``. The left operand is deep-copied
        so the two MUL children are distinct nodes.

        :param expr: An EXP expression node with both children present.
        :type expr: Expression
        :return: A new MUL node when the pattern applies, otherwise *expr*.
        :rtype: Expression
        '''

        # Bail out if the tree is malformed.
        if expr.left is None or expr.right is None:
            return expr

        # Only the exact literal 2 triggers this rewrite.
        if not self.is_literal_two(expr.right):
            return expr

        left_copy = self.deep_copy_expr(expr.left)
        return ExpressionAggregate(
            kind=ExprKind.MUL,
            value='*',
            left=expr.left,
            right=left_copy,
            lineno=expr.lineno,
            col=expr.col,
        )


# ** util: return_analyzer
class ReturnAnalyzer(ReturnAnalyzerService):
    '''
    Concrete AST analyzer that detects statements following a ``return``
    within the same scope and reports them as unreachable-code warnings.

    The analyzer performs a non-mutating walk of the declaration tree,
    maintaining a scope stack so warnings carry a qualified
    ``scope_path``. Every ``return`` statement terminates the remainder
    of its enclosing statement chain; any statements on that chain after
    the return are flagged as ``UNREACHABLE_AFTER_RETURN``.

    In addition to direct returns, an ``if_else`` statement whose
    ``body`` and ``else_body`` chains both provably end in a ``return``
    is also treated as a terminator so that siblings following such a
    construct are flagged as unreachable. ``for``, ``while``, and
    ``snippet`` chains are not treated as terminators.
    '''

    # * attribute: warnings
    warnings: List[Dict]

    # * attribute: scope_stack
    scope_stack: List[str]

    # * init
    def __init__(self):
        '''
        Initialize the return analyzer with empty state.
        '''

        # Prepare the warning accumulator and scope stack.
        self.warnings = []
        self.scope_stack = []

    # * method: analyze
    def analyze(self, ast: Declaration) -> List[Dict]:
        '''
        Entry point: walk the full AST and collect dead-code warnings.

        :param ast: The root DeclarationAggregate produced by the parser.
        :type ast: Declaration
        :return: List of warning dicts (empty when no dead code is found).
        :rtype: List[Dict]
        '''

        # Reset state so repeated calls are idempotent.
        self.warnings = []
        self.scope_stack = ['module']

        # Walk the module declaration chain.
        self.walk_declaration(ast)

        # Return the collected warnings.
        return list(self.warnings)

    # * method: current_scope_path
    @property
    def current_scope_path(self) -> str:
        '''
        Return the dotted path of the currently-enclosing scope.

        :return: The scope path (e.g. ``module.EventClass.execute``).
        :rtype: str
        '''

        return '.'.join(self.scope_stack) if self.scope_stack else 'module'

    # * method: walk_declaration
    def walk_declaration(self, decl: Optional[Declaration]) -> None:
        '''
        Recursively analyze a declaration chain, pushing a scope for each
        class or function declaration encountered.

        :param decl: A Declaration node, or None to stop recursion.
        :type decl: Declaration | None
        '''

        # Base case: nothing to analyze.
        if decl is None:
            return

        # Determine whether this declaration introduces a new scope.
        kind = decl.type.kind if decl.type else None
        pushes_scope = kind in (TypeKind.CLASS, TypeKind.FUNC)

        # Enter the new scope if applicable.
        if pushes_scope and decl.name:
            self.scope_stack.append(decl.name)

        # Recurse into the body of this declaration.
        if decl.code is not None:
            self.scan_block(decl.code)

        # Leave the scope if one was entered.
        if pushes_scope and decl.name:
            self.scope_stack.pop()

        # Continue to the next declaration in the chain.
        if decl.next is not None:
            self.walk_declaration(decl.next)

    # * method: scan_block
    def scan_block(self, stmt: Optional[Statement]) -> None:
        '''
        Walk a statement chain, flagging statements that follow a
        terminator (return, or if/else whose branches both return) as
        unreachable. ``SNIPPET`` and ``BLOCK`` containers are flattened
        transparently so a return inside one snippet correctly terminates
        statements grouped into a sibling snippet by the parser.

        :param stmt: The first Statement in the chain, or None.
        :type stmt: Statement | None
        '''

        # Base case: empty chain.
        if stmt is None:
            return

        # Track the terminating statement (return or provably-returning
        # if/else) so following statements can be flagged against it.
        terminator: Optional[Statement] = None
        for current in self.iter_effective_statements(stmt):

            # Comments never contribute to control flow and must not be
            # reported as unreachable code either.
            if current.kind == StatementKind.COMMENT:
                continue

            # Recurse into inner scopes on every statement regardless of
            # terminator state, so unreachable code inside earlier
            # branches is still analyzed.
            self.descend(current)

            # When a terminator was already seen earlier in this chain,
            # everything from here on is unreachable within this scope.
            if terminator is not None:
                self.flag_unreachable(current, terminator)
                continue

            # A direct return terminates the remainder of this chain.
            if current.kind == StatementKind.RETURN:
                terminator = current
                continue

            # An if/else whose both branches always return also terminates.
            if (
                current.kind == StatementKind.IF_ELSE
                and self.block_always_returns(current.body)
                and self.block_always_returns(current.else_body)
            ):
                terminator = current
                continue

    # * method: iter_effective_statements
    def iter_effective_statements(self, stmt: Optional[Statement]):
        '''
        Yield the effective statements of a chain, transparently
        flattening ``SNIPPET`` and ``BLOCK`` container statements so the
        parser's grouping of consecutive lines does not hide terminators
        from sibling statements at the logical enclosing scope.

        :param stmt: The first Statement in the chain, or None.
        :type stmt: Statement | None
        '''

        # Walk the .next chain, flattening containers inline.
        current = stmt
        while current is not None:
            if current.kind in (StatementKind.SNIPPET, StatementKind.BLOCK):
                yield from self.iter_effective_statements(current.body)
            else:
                yield current
            current = current.next

    # * method: descend
    def descend(self, stmt: Statement) -> None:
        '''
        Recurse into a statement's nested bodies and inline declarations
        so nested blocks are analyzed independently from their enclosing
        chain. Each nested chain has its own terminator semantics.

        :param stmt: The statement whose children should be visited.
        :type stmt: Statement
        '''

        # Inline declarations (decl statements) may open a new scope.
        if stmt.decl is not None:
            self.walk_declaration(stmt.decl)

        # Recurse into statement bodies (if/else, for, while, artifact).
        if stmt.body is not None:
            self.scan_block(stmt.body)

        # Recurse into else branches.
        if stmt.else_body is not None:
            self.scan_block(stmt.else_body)

    # * method: flag_unreachable
    def flag_unreachable(self, stmt: Statement, terminator: Statement) -> None:
        '''
        Record an ``UNREACHABLE_AFTER_RETURN`` warning for *stmt* whose
        predecessor in the chain was *terminator*.

        :param stmt: The unreachable statement.
        :type stmt: Statement
        :param terminator: The return (or terminating if/else) statement
            that makes *stmt* unreachable.
        :type terminator: Statement
        '''

        # Build the warning dict mirroring the TypeChecker shape.
        warning = {
            'warning_code': UNREACHABLE_AFTER_RETURN_CODE,
            'message': UNREACHABLE_AFTER_RETURN_MESSAGE,
            'scope_path': self.current_scope_path,
        }

        # Attach position info for the unreachable statement.
        if stmt.lineno is not None:
            warning['lineno'] = stmt.lineno
        if stmt.col is not None:
            warning['col'] = stmt.col

        # Attach position info for the triggering terminator.
        if terminator.lineno is not None:
            warning['return_lineno'] = terminator.lineno
        if terminator.col is not None:
            warning['return_col'] = terminator.col

        # Record the warning.
        self.warnings.append(warning)

    # * method: block_always_returns
    def block_always_returns(self, stmt: Optional[Statement]) -> bool:
        '''
        Return True when the statement chain rooted at *stmt* is
        guaranteed to terminate in a ``return`` along every path.

        A chain terminates when its final effective statement (after
        flattening ``SNIPPET`` / ``BLOCK`` containers and ignoring pure
        comment statements) is a ``return`` or when it is an ``if_else``
        whose both branches also always return.

        :param stmt: The first statement of the chain, or None.
        :type stmt: Statement | None
        :return: True when the chain always reaches a return.
        :rtype: bool
        '''

        # Empty chains cannot guarantee a return.
        if stmt is None:
            return False

        # Walk the effective (flattened) chain and retain the last
        # non-comment statement seen.
        last: Optional[Statement] = None
        for current in self.iter_effective_statements(stmt):
            if current.kind == StatementKind.COMMENT:
                continue
            last = current

        # Empty or comment-only chains cannot guarantee a return.
        if last is None:
            return False

        # A trailing return terminates the chain.
        if last.kind == StatementKind.RETURN:
            return True

        # A trailing if/else terminates only when both branches always return.
        if last.kind == StatementKind.IF_ELSE:
            return (
                self.block_always_returns(last.body)
                and self.block_always_returns(last.else_body)
            )

        # Any other trailing statement does not guarantee termination.
        return False
