"""AST Utility Base Classes"""

# *** imports

# ** core
from typing import Optional

# ** app
from ..domain.ast import Declaration, Statement, Expression

# *** utils

# ** class: ast_traversal
class ASTTraversal:
    '''
    Base traversal skeleton for AST transformation and analysis passes.

    Provides concrete ``traverse_declaration`` and ``traverse_statement``
    methods that walk every node in the declaration and statement chains,
    including ``code``, ``body``, ``else_body``, and ``.next`` links. For
    each expression field encountered during the walk, the traversal calls
    the ``transform_expression`` hook so that subclasses can apply their
    per-expression rewrite logic without duplicating the traversal skeleton.

    Concrete optimizer classes (e.g. ``ConstantFolder``, ``StrengthReducer``)
    extend this class, inherit the shared traversal, and override
    ``transform_expression`` to route into their own expression-level method.
    '''

    # * method: traverse_declaration
    def traverse_declaration(self, decl: Optional[Declaration]) -> None:
        '''
        Walk a declaration chain, applying ``transform_expression`` to any
        expression fields encountered and recursing into code blocks and the
        ``next`` sibling chain.

        :param decl: The first Declaration node in the chain, or None.
        :type decl: Declaration | None
        '''

        # Base case: nothing to traverse.
        if decl is None:
            return

        # Transform the declaration value field, if present.
        if decl.value is not None:
            decl.value = self.transform_expression(decl.value)

        # Recurse into the code block of the declaration.
        if decl.code is not None:
            self.traverse_statement(decl.code)

        # Continue to the next declaration in the chain.
        if decl.next is not None:
            self.traverse_declaration(decl.next)

    # * method: traverse_statement
    def traverse_statement(self, stmt: Optional[Statement]) -> None:
        '''
        Walk a statement chain, applying ``transform_expression`` to each
        expression field and recursing into nested bodies and inline
        declarations.

        :param stmt: The first Statement node in the chain, or None.
        :type stmt: Statement | None
        '''

        # Base case: nothing to traverse.
        if stmt is None:
            return

        # Recurse into inline declarations (e.g. DECL statements).
        if stmt.decl is not None:
            self.traverse_declaration(stmt.decl)

        # Transform the primary expression of the statement.
        if stmt.expr is not None:
            stmt.expr = self.transform_expression(stmt.expr)

        # Transform the initialisation expression (e.g. for-loop range).
        if stmt.init_expr is not None:
            stmt.init_expr = self.transform_expression(stmt.init_expr)

        # Recurse into statement bodies (if-else, for, while, snippet).
        if stmt.body is not None:
            self.traverse_statement(stmt.body)

        # Recurse into the else branch.
        if stmt.else_body is not None:
            self.traverse_statement(stmt.else_body)

        # Continue to the next statement in the chain.
        if stmt.next is not None:
            self.traverse_statement(stmt.next)

    # * method: transform_expression
    def transform_expression(self, expr: Optional[Expression]) -> Optional[Expression]:
        '''
        Expression transformation hook invoked by the traversal for every
        expression field it encounters.

        The default implementation returns *expr* unchanged. Subclasses
        override this method to route into their own expression-level
        rewrite logic (e.g. ``fold_expression``, ``reduce_expression``)
        without duplicating the declaration and statement traversal.

        :param expr: The expression node to transform, or None.
        :type expr: Expression | None
        :return: The transformed expression, or the original if unchanged.
        :rtype: Expression | None
        '''

        # Default: return the expression unchanged.
        return expr
