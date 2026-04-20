"""Optimizer Utilities: YAML Anchor/Alias and Constant Folding"""

# *** imports

# ** core
from typing import Any, Dict, List, Optional, Tuple

# ** app
from ..domain.ast import Declaration, Expression, Statement, ExprKind
from ..interfaces.optimizer import OptimizerService, ASTOptimizerService
from ..mappers.ast import ExpressionAggregate

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
