"""Scanner Parser Utility"""

# *** imports

# ** core
from typing import List, Dict, Any

# ** infra
import ply.yacc as yacc

# ** app
from ..events import a
from ..interfaces import ParserService
from ..mappers import TokenAggregate, DeclAggragate as Decl
from ..mappers.ast import ExpressionAggregate as Expr, StatementAggregate as Stmt

# *** utils

# ** util: token_stream
class TokenStream:
    '''
    Adapter to convert a list of TokenAggregate objects into a token stream compatible with PLY's parsing interface. 
    This allows us to feed the output of the TiferetLexer directly into the TiferetParser without needing to convert 
    to an intermediate format. The TokenStream implements a .token() method that PLY expects, returning the next token 
    or None at the end of the stream.
    '''

    # * attribute: iter
    iter: Any

    # * init
    def __init__(self, tokens: List[TokenAggregate]):
        '''
        Initialize the token stream adapter.

        :param tokens: The list of token aggregates to be adapted for PLY parsing.
        :type tokens: List[TokenAggregate]
        '''

        self.iter = iter(tokens)

    # * method: token
    def token(self):
        '''
        Return the next token as a PLY-compatible object, or None at end of stream.

        :return: A PLY-compatible token object or None.
        :rtype: object | None
        '''

        # Define a simple PLY token class for compatibility. In a full implementation, this would need to include all attributes PLY expects.
        class PLYToken:
            pass

        try:
            token = next(self.iter)
            ply_token = PLYToken()
            ply_token.type = token.type
            ply_token.value = token.value
            ply_token.lineno = token.lineno
            ply_token.lexpos = token.lexpos
            return ply_token
        except StopIteration:
            return None

# ** util: parser_base
class ParserBase(ParserService):
    '''
    Base class for Tiferet parsers, providing common utilities and structure for parsing events. This can be extended by specific parser implementations (e.g., TiferetParser) to implement the actual parsing logic while sharing common functionality.
    '''

    # * attribute: parser
    parser: Any

    # -- PLY token list (sourced from assets)
    tokens = a.parser.TOKENS

    # -- PLY precedence (sourced from assets)
    precedence = a.parser.precedence

    # * init
    def __init__(self):
        '''
        Initialize the parser base. This can include setting up common state or utilities needed by all parsers.
        '''
        
        self.parser_service = yacc.yacc(module=self, start='module', debug=False, write_tables=False)

    # * method: parse
    def parse(self, module_name: str, tokens: List[TokenAggregate]) -> Dict[str, Any]:
        '''
        Parse a list of token dictionaries (post-IndentInjector) into AST.

        :param module_name: The name of the module being parsed.
        :type module_name: str
        :param tokens: Token stream with 'type' and 'value' keys.
        :type tokens: List[TokenAggregate]
        :return: Structured AST dict reflecting the three-tier artifact hierarchy.
        :rtype: Dict[str, Any]
        '''
        
        # Convert the list of TokenAggregate objects into a PLY-compatible token stream.
        token_stream = TokenStream(tokens)

        # Parse the token stream and return the AST.
        return self.parser_service.parse(lexer=token_stream)
    
    # * method: parse_member_kind (helper)
    @staticmethod
    def parse_member_kind(artifact_member_value: str) -> str:
        '''
        Extract the member kind from an ARTIFACT_MEMBER token value.
        E.g. "# * attribute: error_service" -> "attribute",
             "# * init" -> "init",
             "# * method: execute" -> "method".

        :param artifact_member_value: The raw ARTIFACT_MEMBER token value.
        :type artifact_member_value: str
        :return: The member kind string.
        :rtype: str
        '''

        # Strip the "# * " prefix and extract the first word.
        stripped = artifact_member_value.lstrip('# *').strip()
        kind = stripped.split(':')[0].split()[0] if stripped else 'unknown'
        return kind

    # * method: p_error
    def p_error(self, p):
        '''
        Report syntax errors using Tiferet artifact hierarchy terminology.
        '''

        if p:
            raise SyntaxError(
                f"Syntax error in Tiferet artifact hierarchy: "
                f"unexpected token '{p.type}' "
                f"(value={p.value!r}, line {getattr(p, 'lineno', '?')}). "
                f"Expected a valid # *** Group, # ** Section, or # * Member structure."
            )
        else:
            raise SyntaxError(
                "Unexpected end of input while parsing Tiferet Domain Event structure. "
                "Ensure all # *** Group, # ** Section, and # * Member blocks are complete."
            )

# ** util: tiferet_parser
class TiferetParser(ParserBase):
    '''
    PLY-based parser for the Tiferet Domain Event dialect. Implements ParserService and defines the grammar rules to parse the token stream into a structured AST reflecting the three-tier artifact hierarchy.
    '''

    # -- Tier 1: Module / Artifact Groups --

    # * method: p_module (rule)
    def p_module(self, p):
        '''module : group_list'''

        # Build Module AST node from group list.
        p[0] = a.parser.build_module(p[1])

    # * method: p_module_doc (rule)
    def p_module_doc(self, p):
        '''module : DOCSTRING NEWLINE group_list'''

        # Build Module AST node with docstring.
        p[0] = a.parser.build_module(p[3], docstring=p[1])

    # * method: p_group_list (rule)
    def p_group_list(self, p):
        '''group_list : group_list group'''

        # Collect groups into a list via left-recursive accumulation.
        p[0] = p[1] + [p[2]]

    # * method: p_group_list_empty (rule)
    def p_group_list_empty(self, p):
        '''group_list : '''

        # Initialize an empty group list.
        p[0] = []

    # * method: p_group (rule)
    def p_group(self, p):
        '''group : group_header NEWLINE section_list'''

        # Build Group AST node: header NEWLINE section_list.
        p[0] = Stmt.new_artifact_stmt(p[1], p[3])

    # * method: p_group_header_imports (rule)
    def p_group_header_imports(self, p):
        '''group_header : ARTIFACT_IMPORTS_START'''

        # Parse the group header token value.
        _, type, name = p[1].split()
        p[0] = Decl.new_artifact_decl(name, type)

    # * method: p_group_header_start (rule)
    def p_group_header_start(self, p):
        '''group_header : ARTIFACT_START'''

        # Parse the group header token value.
        _, type, name = p[1].split()
        p[0] = Decl.new_artifact_decl(name, type)

    # -- Tier 2: Artifact Sections --

    # * method: p_section_list (rule)
    def p_section_list(self, p):
        '''section_list : section_list section'''

        # Collect sections via linked-list accumulation.
        if p[1]:
            p[1].set_next(p[2])
            p[0] = p[1]
        else:
            p[0] = p[2]

    # * method: p_section_list_empty (rule)
    def p_section_list_empty(self, p):
        '''section_list : '''

        # Initialize an empty section list.
        p[0] = []

    # * method: p_section (rule)
    def p_section(self, p):
        '''section : section_header NEWLINE section_body'''

        # Build Section AST node: header NEWLINE body.
        p[0] = Stmt.new_artifact_stmt(p[1], p[3])

    # * method: p_section_annotated (rule)
    def p_section_annotated(self, p):
        '''section : annots section_header NEWLINE section_body'''

        # Build Section AST node with annotations: annots header NEWLINE body.
        p[0] = a.parser.build_section(p[2], p[4], annotations=p[1])

    # * method: p_section_post_annotated (rule)
    def p_section_post_annotated(self, p):
        '''section : section_header NEWLINE annots section_body'''

        # Build Section AST node with post-header annotations: header NEWLINE annots body.
        p[0] = a.parser.build_section(p[1], p[4], annotations=p[3])

    # * method: p_section_header_section (rule)
    def p_section_header_section(self, p):
        '''section_header : ARTIFACT_SECTION'''

        # Parse the section header token value.
        try:
            _, type, name = p[1].split()
        except ValueError:
            _, type, name = p[1].split(maxsplit=2)
        p[0] = Decl.new_artifact_decl(name, type)

    # * method: p_section_header_import (rule)
    def p_section_header_import(self, p):
        '''section_header : ARTIFACT_IMPORT_GROUP'''

        # Parse the section header token value.
        try:
            _, type, name = p[1].split()
        except ValueError:
            _, type, name = p[1].split(maxsplit=2)
        p[0] = Decl.new_artifact_decl(name, type)

    # * method: p_annots_single (rule)
    def p_annots_single(self, p):
        '''annots : annot'''

        # Start an annotation list from a single annotation.
        p[0] = [p[1]]

    # * method: p_annots_multi (rule)
    def p_annots_multi(self, p):
        '''annots : annots annot'''

        # Extend an annotation list with an additional annotation.
        p[0] = p[1] + [p[2]]

    # * method: p_annot_obsolete (rule)
    def p_annot_obsolete(self, p):
        '''annot : OBSOLETE NEWLINE'''

        # Build OBSOLETE annotation node.
        p[0] = a.parser.build_annot('OBSOLETE', p[1])

    # * method: p_annot_todo (rule)
    def p_annot_todo(self, p):
        '''annot : TODO NEWLINE'''

        # Build TODO annotation node.
        p[0] = a.parser.build_annot('TODO', p[1])

    # -- Section Body --

    # * method: p_section_body_class (rule)
    def p_section_body_class(self, p):
        '''section_body : class_def'''

        # Pass through the section body.
        p[0] = p[1]

    # * method: p_section_body_func (rule)
    def p_section_body_func(self, p):
        '''section_body : func_def'''

        # Pass through the section body.
        p[0] = p[1]

    # * method: p_section_body_import (rule)
    def p_section_body_import(self, p):
        '''section_body : import_block'''

        # Pass through the section body.
        p[0] = p[1]

    # * method: p_import_block_single (rule)
    def p_import_block_single(self, p):
        '''import_block : import_stmt'''

        # Pass through a single import statement as an import block.
        p[0] = p[1]

    # * method: p_import_block_multi (rule)
    def p_import_block_multi(self, p):
        '''import_block : import_block import_stmt'''

        # Extend an import block with an additional import statement.
        p[1].set_next(p[2])
        p[0] = p[1]

    # * method: p_import_stmt (rule)
    def p_import_stmt(self, p):
        '''import_stmt : IMPORT import_expr NEWLINE'''

        # Build ImportStmt node.
        p[0] = Stmt.new_import_stmt(p[2])

    # * method: p_import_stmt_from (rule)
    def p_import_stmt_from(self, p):
        '''import_stmt : FROM from_expr IMPORT import_expr NEWLINE'''

        # Build ImportFromStmt node.
        p[0] = Stmt.new_import_stmt_from(p[2], p[4])

    # * method: p_import_expr (rule)
    def p_import_expr(self, p):
        '''import_expr : IDENTIFIER'''

        # Build ImportExpr name node.
        p[0] = Expr.new_name_expr(p[1])

    # * method: p_import_expr_as (rule)
    def p_import_expr_as(self, p):
        '''import_expr : import_expr AS IDENTIFIER'''

        # Build ImportExpr with alias.
        p[0] = Expr.new_import_expr_as(p[1], p[3])

    # * method: p_import_expr_multi (rule)
    def p_import_expr_multi(self, p):
        '''import_expr : import_expr COMMA IDENTIFIER'''

        # Build ImportExpr with multiple names.
        p[0] = Expr.new_import_expr_multi(p[1], p[3])

    # * method: p_from_expr (rule)
    def p_from_expr(self, p):
        '''from_expr : IDENTIFIER'''

        # Build FromExpr name node.
        p[0] = Expr.new_name_expr(p[1])

    # * method: p_from_expr_dot (rule)
    def p_from_expr_dot(self, p):
        '''from_expr : DOT from_expr'''

        # Build FromExpr with dot notation.
        p[2].name = '.' + p[2].name
        p[0] = p[2]

    # -- Class Definition --

    # * method: p_class_def (rule)
    def p_class_def(self, p):
        '''class_def : CLASS IDENTIFIER LPAREN name_list RPAREN COLON NEWLINE INDENT class_body DEDENT'''

        # Build ClassDef AST node.
        p[0] = a.parser.build_class_def(
            name=p[2],
            bases=p[4],
            body=p[9]['members'],
            docstring=p[9].get('docstring'),
        )

    # * method: p_class_body_doc (rule)
    def p_class_body_doc(self, p):
        '''class_body : DOCSTRING NEWLINE member_list'''

        # Build ClassBody with docstring.
        p[0] = {'docstring': p[1], 'members': p[3]}

    # * method: p_class_body_nodoc (rule)
    def p_class_body_nodoc(self, p):
        '''class_body : member_list'''

        # Build ClassBody without docstring.
        p[0] = {'docstring': None, 'members': p[1]}

    # * method: p_name_list_single (rule)
    def p_name_list_single(self, p):
        '''name_list : IDENTIFIER'''

        # Start a name list with a single identifier.
        p[0] = [p[1]]

    # * method: p_name_list_multi (rule)
    def p_name_list_multi(self, p):
        '''name_list : name_list COMMA IDENTIFIER'''

        # Extend a name list.
        p[0] = p[1] + [p[3]]

    # -- Tier 3: Artifact Members --

    # * method: p_member_list (rule)
    def p_member_list(self, p):
        '''member_list : member_list member'''

        # Collect members into a list via left-recursive accumulation.
        p[0] = p[1] + [p[2]]

    # * method: p_member_list_empty (rule)
    def p_member_list_empty(self, p):
        '''member_list : '''

        # Initialize an empty member list.
        p[0] = []

    # * method: p_member (rule)
    def p_member(self, p):
        '''member : ARTIFACT_MEMBER NEWLINE member_body'''

        # Build Member AST node.
        kind = self.parse_member_kind(p[1])
        p[0] = a.parser.build_member(kind, p[3])

    # * method: p_member_annotated (rule)
    def p_member_annotated(self, p):
        '''member : annots ARTIFACT_MEMBER NEWLINE member_body'''

        # Build Member AST node with annotations.
        kind = self.parse_member_kind(p[2])
        p[0] = a.parser.build_member(kind, p[4], annotations=p[1])

    # * method: p_member_post_annotated (rule)
    def p_member_post_annotated(self, p):
        '''member : ARTIFACT_MEMBER NEWLINE annots member_body'''

        # Build Member AST node with post-header annotations.
        kind = self.parse_member_kind(p[1])
        p[0] = a.parser.build_member(kind, p[4], annotations=p[3])

    # * method: p_member_body_attr (rule)
    def p_member_body_attr(self, p):
        '''member_body : attr_decl'''

        # Pass through the member body.
        p[0] = p[1]

    # * method: p_member_body_method (rule)
    def p_member_body_method(self, p):
        '''member_body : method_def'''

        # Pass through the member body.
        p[0] = p[1]

    # * method: p_attr_decl (rule)
    def p_attr_decl(self, p):
        '''attr_decl : IDENTIFIER COLON token_seq NEWLINE'''

        # Build AttrDecl AST node.
        p[0] = a.parser.build_attr_decl(p[1], p[3])

    # -- Method Definition --

    # * method: p_method_def (rule)
    def p_method_def(self, p):
        '''method_def : DEF method_name LPAREN SELF param_tail RPAREN ret_annot COLON NEWLINE INDENT body DEDENT'''

        # Build MethodDef AST node.
        p[0] = a.parser.build_method_def(
            name=p[2],
            params=p[5],
            body=p[11]['snippets'],
            return_type=p[7],
            docstring=p[11].get('docstring'),
        )

    # * method: p_method_def_decorated (rule)
    def p_method_def_decorated(self, p):
        '''method_def : decorator DEF method_name LPAREN SELF param_tail RPAREN ret_annot COLON NEWLINE INDENT body DEDENT'''

        # Build decorated MethodDef AST node.
        p[0] = a.parser.build_method_def(
            name=p[3],
            params=p[6],
            body=p[12]['snippets'],
            return_type=p[8],
            decorator=p[1],
            docstring=p[12].get('docstring'),
        )

    # * method: p_method_name_id (rule)
    def p_method_name_id(self, p):
        '''method_name : IDENTIFIER'''

        # Pass through method name.
        p[0] = p[1]

    # * method: p_method_name_init (rule)
    def p_method_name_init(self, p):
        '''method_name : INIT'''

        # Pass through method name.
        p[0] = p[1]

    # * method: p_param_tail (rule)
    def p_param_tail(self, p):
        '''param_tail : COMMA token_seq'''

        # Build param tail.
        p[0] = p[2]

    # * method: p_param_tail_empty (rule)
    def p_param_tail_empty(self, p):
        '''param_tail : '''

        # Build empty param tail.
        p[0] = []

    # * method: p_ret_annot (rule)
    def p_ret_annot(self, p):
        '''ret_annot : ARROW token_seq'''

        # Build return annotation.
        p[0] = p[2]

    # * method: p_ret_annot_empty (rule)
    def p_ret_annot_empty(self, p):
        '''ret_annot : '''

        # Build empty return annotation.
        p[0] = None

    # * method: p_decorator (rule)
    def p_decorator(self, p):
        '''decorator : AT token_seq NEWLINE'''

        # Build Decorator AST node.
        p[0] = a.parser.build_decorator(p[2])

    # -- Function Definition --

    # * method: p_func_def (rule)
    def p_func_def(self, p):
        '''func_def : DEF IDENTIFIER LPAREN param_body RPAREN ret_annot COLON NEWLINE INDENT body DEDENT'''

        # Build FuncDef AST node.
        p[0] = a.parser.build_func_def(
            name=p[2],
            params=p[4],
            body=p[10]['snippets'],
            return_type=p[6],
            docstring=p[10].get('docstring'),
        )

    # * method: p_func_def_decorated (rule)
    def p_func_def_decorated(self, p):
        '''func_def : decorator DEF IDENTIFIER LPAREN param_body RPAREN ret_annot COLON NEWLINE INDENT body DEDENT'''

        # Build decorated FuncDef AST node.
        p[0] = a.parser.build_func_def(
            name=p[3],
            params=p[5],
            body=p[11]['snippets'],
            return_type=p[7],
            decorator=p[1],
            docstring=p[11].get('docstring'),
        )

    # * method: p_param_body (rule)
    def p_param_body(self, p):
        '''param_body : token_seq'''

        # Pass through param body.
        p[0] = p[1]

    # * method: p_param_body_empty (rule)
    def p_param_body_empty(self, p):
        '''param_body : '''

        # Build empty param body.
        p[0] = []

    # -- Body / Snippets --

    # * method: p_body_doc (rule)
    def p_body_doc(self, p):
        '''body : DOCSTRING NEWLINE snippet_list'''

        # Build Body with docstring.
        p[0] = a.parser.build_body(p[3], docstring=p[1])

    # * method: p_body_nodoc (rule)
    def p_body_nodoc(self, p):
        '''body : snippet_list'''

        # Build Body without docstring.
        p[0] = a.parser.build_body(p[1])

    # * method: p_snippet_list (rule)
    def p_snippet_list(self, p):
        '''snippet_list : snippet_list snippet'''

        # Collect snippets into a list via left-recursive accumulation.
        p[0] = p[1] + [p[2]]

    # * method: p_snippet_list_empty (rule)
    def p_snippet_list_empty(self, p):
        '''snippet_list : '''

        # Initialize an empty snippet list.
        p[0] = []

    # * method: p_snippet_comment (rule)
    def p_snippet_comment(self, p):
        '''snippet : LINE_COMMENT NEWLINE stmt_list'''

        # Build Snippet with comment.
        p[0] = a.parser.build_snippet(p[3], comment=p[1])

    # * method: p_snippet_nocomment (rule)
    def p_snippet_nocomment(self, p):
        '''snippet : stmt_list'''

        # Build Snippet without comment.
        p[0] = a.parser.build_snippet(p[1])

    # * method: p_stmt_list (rule)
    def p_stmt_list(self, p):
        '''stmt_list : stmt_list stmt'''

        # Collect statements into a list via left-recursive accumulation.
        p[0] = p[1] + [p[2]]

    # * method: p_stmt_list_empty (rule)
    def p_stmt_list_empty(self, p):
        '''stmt_list : '''

        # Initialize an empty statement list.
        p[0] = []

    # * method: p_stmt_simple (rule)
    def p_stmt_simple(self, p):
        '''stmt : token_seq NEWLINE'''

        # Build simple Stmt.
        p[0] = a.parser.build_stmt(p[1])

    # * method: p_stmt_compound (rule)
    def p_stmt_compound(self, p):
        '''stmt : token_seq NEWLINE INDENT stmt_list DEDENT'''

        # Build compound Stmt with indented sub-block.
        p[0] = a.parser.build_stmt(p[1], block=p[4])

    # -- Token Sequence --

    # * method: p_token_seq_single (rule)
    def p_token_seq_single(self, p):
        '''token_seq : token_item'''

        # Start a token sequence with a single item.
        p[0] = [p[1]]

    # * method: p_token_seq_multi (rule)
    def p_token_seq_multi(self, p):
        '''token_seq : token_seq token_item'''

        # Extend a token sequence with an additional item.
        p[0] = p[1] + [p[2]]

    # * method: p_token_item_token (rule)
    def p_token_item_token(self, p):
        '''token_item : token'''

        # Pass through token item.
        p[0] = p[1]

    # * method: p_token_item_enclosed (rule)
    def p_token_item_enclosed(self, p):
        '''token_item : enclosed'''

        # Pass through token item.
        p[0] = p[1]

    # * method: p_enclosed_paren (rule)
    def p_enclosed_paren(self, p):
        '''enclosed : LPAREN inner RPAREN'''

        # Build Enclosed AST node.
        p[0] = a.parser.build_enclosed(p[1], p[2], p[3])

    # * method: p_enclosed_brack (rule)
    def p_enclosed_brack(self, p):
        '''enclosed : LBRACK inner RBRACK'''

        # Build Enclosed AST node.
        p[0] = a.parser.build_enclosed(p[1], p[2], p[3])

    # * method: p_enclosed_brace (rule)
    def p_enclosed_brace(self, p):
        '''enclosed : LBRACE inner RBRACE'''

        # Build Enclosed AST node.
        p[0] = a.parser.build_enclosed(p[1], p[2], p[3])

    # * method: p_inner (rule)
    def p_inner(self, p):
        '''inner : inner inner_item'''

        # Extend inner items.
        p[0] = p[1] + [p[2]]

    # * method: p_inner_empty (rule)
    def p_inner_empty(self, p):
        '''inner : '''

        # Initialize empty inner.
        p[0] = []

    # * method: p_inner_item_token (rule)
    def p_inner_item_token(self, p):
        '''inner_item : token_item'''

        # Pass through inner item.
        p[0] = p[1]

    # * method: p_inner_item_newline (rule)
    def p_inner_item_newline(self, p):
        '''inner_item : NEWLINE'''

        # Pass through inner item.
        p[0] = p[1]

    # -- Token Catch-All --

    # * method: p_token (rule)
    def p_token(self, p):
        '''token : IDENTIFIER
                 | SELF
                 | INIT
                 | RETURN
                 | CLASS
                 | DEF
                 | STRING_LITERAL
                 | NUMBER_LITERAL
                 | DOCSTRING
                 | PYTHON_KEYWORD
                 | DOT
                 | COMMA
                 | COLON
                 | EQUALS
                 | ARROW
                 | PLUS
                 | MINUS
                 | STAR
                 | DOUBLESTAR
                 | SLASH
                 | DOUBLESLASH
                 | PERCENT
                 | PIPE
                 | AMPERSAND
                 | TILDE
                 | CARET
                 | LSHIFT
                 | RSHIFT
                 | EQEQ
                 | NOTEQ
                 | LTEQ
                 | GTEQ
                 | LT
                 | GT
                 | AT
                 | UNKNOWN'''

        # Pass through a content terminal value.
        p[0] = p[1]

