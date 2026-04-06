"""Scanner Parser Utility"""

# *** imports

# ** core
from types import MethodType
from typing import List, Dict, Any

# ** infra
import ply.yacc as yacc

# ** app
from ..events import a
from ..interfaces import ParserService

# *** utils

# ** util: tiferet_parser
class TiferetParser(ParserService):
    '''
    PLY yacc-based syntactic parser for the Tiferet Domain Event dialect.
    Implements ParserService and dynamically loads grammar from assets,
    exactly mirroring the TiferetLexer pattern.
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
        Initialize the TiferetParser by dynamically attaching grammar rules
        and building the PLY yacc instance.
        '''

        # Load rules dynamically from the assets mapping (mirrors lexer).
        for name, rule in a.parser.RULES.items():
            if callable(rule):
                setattr(self, name, MethodType(rule, self))
            else:
                # String BNF rule — create a wrapper with __doc__ set to the production.
                handler = _build_semantic_action(name, rule)
                setattr(self, name, MethodType(handler, self))

        # Build the PLY yacc parser.
        self.parser = yacc.yacc(module=self, start='module', debug=False, write_tables=False)

    # * method: parse
    def parse(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        '''
        Parse a list of token dictionaries (post-IndentInjector) into AST.

        :param tokens: Token stream with 'type' and 'value' keys.
        :type tokens: List[Dict[str, Any]]
        :return: Structured AST dict reflecting the three-tier artifact hierarchy.
        :rtype: Dict[str, Any]
        '''

        # Create a thin adapter so PLY can consume our List[Dict] token stream.
        stream = TokenStream(tokens)

        # Parse the token stream and return the AST.
        return self.parser.parse(lexer=stream)

    # * rule: error
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


# *** classes

# ** class: token_stream
class TokenStream:
    '''
    Thin adapter that feeds a List[Dict] token stream to PLY's yacc parser.
    PLY calls stream.token() repeatedly until it returns None.
    '''

    # * init
    def __init__(self, tokens: List[Dict[str, Any]]):
        '''
        Initialize the token stream adapter.

        :param tokens: The list of token dictionaries from the lexer + IndentInjector.
        :type tokens: List[Dict[str, Any]]
        '''

        self._iter = iter(tokens)

    # * method: token
    def token(self):
        '''
        Return the next token as a PLY-compatible object, or None at end of stream.

        :return: A PLY-compatible token object or None.
        :rtype: object | None
        '''

        try:
            t = next(self._iter)
            tok = PLYToken()
            tok.type = t['type']
            tok.value = t.get('value')
            tok.lineno = t.get('line', 0)
            tok.lexpos = t.get('column', 0)
            return tok
        except StopIteration:
            return None


# ** class: ply_token
class PLYToken:
    '''
    Minimal PLY-compatible token object used by TokenStream.
    '''

    # * attribute: type
    type: str

    # * attribute: value
    value: Any

    # * attribute: lineno
    lineno: int

    # * attribute: lexpos
    lexpos: int


# *** helpers

# ** helper: _build_semantic_action
def _build_semantic_action(name: str, rule_str: str):
    '''
    Build a semantic action function for a string-based BNF rule.
    The function dispatches to the appropriate AST builder from the parser assets
    based on the rule name.

    :param name: The PLY rule function name (e.g. 'p_module', 'p_group').
    :type name: str
    :param rule_str: The BNF production string used as __doc__.
    :type rule_str: str
    :return: A semantic action function with __doc__ set to the production.
    :rtype: callable
    '''

    # Resolve the semantic action based on the rule name.
    action = _SEMANTIC_ACTIONS.get(name, _default_action)

    # Wrap the action with the production docstring.
    def p_func(self, p):
        action(p)
    p_func.__doc__ = rule_str

    return p_func


# ** helper: _default_action
def _default_action(p):
    '''
    Default semantic action: pass through the first symbol's value.

    :param p: The PLY production object.
    :type p: yacc.YaccProduction
    '''

    p[0] = p[1]


# ** helper: _collect_list
def _collect_list(p):
    '''
    Collect list items via left-recursive accumulation.
    Used for GroupList, SectionList, MemberList, SnippetList, StmtList.

    :param p: The PLY production object.
    :type p: yacc.YaccProduction
    '''

    p[0] = p[1] + [p[2]]


# ** helper: _empty_list
def _empty_list(p):
    '''
    Initialize an empty list for left-recursive base cases.

    :param p: The PLY production object.
    :type p: yacc.YaccProduction
    '''

    p[0] = []


# *** semantic_actions

# ** actions: tier 1 — module / artifact groups

def _action_module(p):
    '''Build Module AST node from group list.'''
    p[0] = a.parser.build_module(p[1])

def _action_group(p):
    '''Build Group AST node: header NEWLINE section_list.'''
    p[0] = a.parser.build_group(p[1], p[3])

def _action_group_header(p):
    '''Pass through the group header token value.'''
    p[0] = p[1]

# ** actions: tier 2 — artifact sections

def _action_section(p):
    '''Build Section AST node: header NEWLINE body.'''
    p[0] = a.parser.build_section(p[1], p[3])

def _action_section_annotated(p):
    '''Build Section AST node with annotations: annots header NEWLINE body.'''
    p[0] = a.parser.build_section(p[2], p[4], annotations=p[1])

def _action_section_header(p):
    '''Pass through the section header token value.'''
    p[0] = p[1]

def _action_annots_single(p):
    '''Start an annotation list from a single annotation.'''
    p[0] = [p[1]]

def _action_annots_multi(p):
    '''Extend an annotation list with an additional annotation.'''
    p[0] = p[1] + [p[2]]

def _action_annot_obsolete(p):
    '''Build OBSOLETE annotation node.'''
    p[0] = a.parser.build_annot('OBSOLETE', p[1])

def _action_annot_todo(p):
    '''Build TODO annotation node.'''
    p[0] = a.parser.build_annot('TODO', p[1])

# ** actions: section body

def _action_section_body(p):
    '''Pass through the section body (ClassDef, FuncDef, or ImportBlock).'''
    p[0] = p[1]

def _action_import_block_single(p):
    '''Start an import block with a single import statement.'''
    p[0] = {'type': 'ImportBlock', 'statements': [p[1]]}

def _action_import_block_multi(p):
    '''Extend an import block with an additional import statement.'''
    p[1]['statements'].append(p[2])
    p[0] = p[1]

def _action_import_stmt(p):
    '''Build ImportStmt: PYTHON_KEYWORD token_seq NEWLINE.'''
    p[0] = a.parser.build_import_stmt(p[1], p[2])

# ** actions: class definition

def _action_class_def(p):
    '''Build ClassDef: CLASS IDENTIFIER LPAREN name_list RPAREN COLON NEWLINE INDENT class_body DEDENT.'''
    p[0] = a.parser.build_class_def(
        name=p[2],
        bases=p[4],
        body=p[9]['members'],
        docstring=p[9].get('docstring'),
    )

def _action_class_body_doc(p):
    '''Build ClassBody with docstring: DOCSTRING NEWLINE member_list.'''
    p[0] = {'docstring': p[1], 'members': p[3]}

def _action_class_body_nodoc(p):
    '''Build ClassBody without docstring: member_list.'''
    p[0] = {'docstring': None, 'members': p[1]}

def _action_name_list_single(p):
    '''Start a name list with a single identifier.'''
    p[0] = [p[1]]

def _action_name_list_multi(p):
    '''Extend a name list: name_list COMMA IDENTIFIER.'''
    p[0] = p[1] + [p[3]]

# ** actions: tier 3 — artifact members

def _action_member(p):
    '''Build Member AST node: ARTIFACT_MEMBER NEWLINE member_body.'''
    kind = _parse_member_kind(p[1])
    p[0] = a.parser.build_member(kind, p[3])

def _action_member_annotated(p):
    '''Build Member AST node with annotations: annots ARTIFACT_MEMBER NEWLINE member_body.'''
    kind = _parse_member_kind(p[2])
    p[0] = a.parser.build_member(kind, p[4], annotations=p[1])

def _action_member_body(p):
    '''Pass through the member body (AttrDecl or MethodDef).'''
    p[0] = p[1]

def _action_attr_decl(p):
    '''Build AttrDecl: IDENTIFIER COLON token_seq NEWLINE.'''
    p[0] = a.parser.build_attr_decl(p[1], p[3])

# ** actions: method definition

def _action_method_def(p):
    '''Build MethodDef: DEF method_name LPAREN SELF param_tail RPAREN ret_annot COLON NEWLINE INDENT body DEDENT.'''
    p[0] = a.parser.build_method_def(
        name=p[2],
        params=p[5],
        body=p[11]['snippets'],
        return_type=p[7],
        docstring=p[11].get('docstring'),
    )

def _action_method_def_decorated(p):
    '''Build decorated MethodDef: decorator DEF method_name LPAREN SELF param_tail RPAREN ret_annot COLON NEWLINE INDENT body DEDENT.'''
    p[0] = a.parser.build_method_def(
        name=p[3],
        params=p[6],
        body=p[12]['snippets'],
        return_type=p[8],
        decorator=p[1],
        docstring=p[12].get('docstring'),
    )

def _action_method_name(p):
    '''Pass through method name (IDENTIFIER or INIT).'''
    p[0] = p[1]

def _action_param_tail(p):
    '''Build param tail: COMMA token_seq.'''
    p[0] = p[2]

def _action_param_tail_empty(p):
    '''Build empty param tail.'''
    p[0] = []

def _action_ret_annot(p):
    '''Build return annotation: ARROW token_seq.'''
    p[0] = p[2]

def _action_ret_annot_empty(p):
    '''Build empty return annotation.'''
    p[0] = None

def _action_decorator(p):
    '''Build Decorator: AT token_seq NEWLINE.'''
    p[0] = a.parser.build_decorator(p[2])

# ** actions: function definition

def _action_func_def(p):
    '''Build FuncDef: DEF IDENTIFIER LPAREN param_body RPAREN ret_annot COLON NEWLINE INDENT body DEDENT.'''
    p[0] = a.parser.build_func_def(
        name=p[2],
        params=p[4],
        body=p[10]['snippets'],
        return_type=p[6],
        docstring=p[10].get('docstring'),
    )

def _action_func_def_decorated(p):
    '''Build decorated FuncDef: decorator DEF IDENTIFIER LPAREN param_body RPAREN ret_annot COLON NEWLINE INDENT body DEDENT.'''
    p[0] = a.parser.build_func_def(
        name=p[3],
        params=p[5],
        body=p[11]['snippets'],
        return_type=p[7],
        decorator=p[1],
        docstring=p[11].get('docstring'),
    )

def _action_param_body(p):
    '''Build param body: token_seq.'''
    p[0] = p[1]

def _action_param_body_empty(p):
    '''Build empty param body.'''
    p[0] = []

# ** actions: body / snippets

def _action_body_doc(p):
    '''Build Body with docstring: DOCSTRING NEWLINE snippet_list.'''
    p[0] = a.parser.build_body(p[3], docstring=p[1])

def _action_body_nodoc(p):
    '''Build Body without docstring: snippet_list.'''
    p[0] = a.parser.build_body(p[1])

def _action_snippet_comment(p):
    '''Build Snippet with comment: LINE_COMMENT NEWLINE stmt_list.'''
    p[0] = a.parser.build_snippet(p[3], comment=p[1])

def _action_snippet_nocomment(p):
    '''Build Snippet without comment: stmt_list.'''
    p[0] = a.parser.build_snippet(p[1])

def _action_stmt_simple(p):
    '''Build simple Stmt: token_seq NEWLINE.'''
    p[0] = a.parser.build_stmt(p[1])

def _action_stmt_compound(p):
    '''Build compound Stmt: token_seq NEWLINE INDENT stmt_list DEDENT.'''
    p[0] = a.parser.build_stmt(p[1], block=p[4])

# ** actions: token sequence

def _action_token_seq_single(p):
    '''Start a token sequence with a single item.'''
    p[0] = [p[1]]

def _action_token_seq_multi(p):
    '''Extend a token sequence with an additional item.'''
    p[0] = p[1] + [p[2]]

def _action_token_item(p):
    '''Pass through a token item (Token or Enclosed).'''
    p[0] = p[1]

def _action_enclosed(p):
    '''Build Enclosed: open inner close.'''
    p[0] = a.parser.build_enclosed(p[1], p[2], p[3])

def _action_inner(p):
    '''Extend inner items: inner inner_item.'''
    p[0] = p[1] + [p[2]]

def _action_inner_empty(p):
    '''Initialize empty inner.'''
    p[0] = []

def _action_inner_item(p):
    '''Pass through inner item (token_item or NEWLINE).'''
    p[0] = p[1]

def _action_token(p):
    '''Pass through a content terminal value.'''
    p[0] = p[1]


# ** helper: _parse_member_kind
def _parse_member_kind(artifact_member_value: str) -> str:
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


# ** constant: semantic_actions
_SEMANTIC_ACTIONS = {
    # -- Tier 1: Module / Artifact Groups --
    'p_module': _action_module,
    'p_group_list': _collect_list,
    'p_group_list_empty': _empty_list,
    'p_group': _action_group,
    'p_group_header_imports': _action_group_header,
    'p_group_header_start': _action_group_header,

    # -- Tier 2: Artifact Sections --
    'p_section_list': _collect_list,
    'p_section_list_empty': _empty_list,
    'p_section': _action_section,
    'p_section_annotated': _action_section_annotated,
    'p_section_header_section': _action_section_header,
    'p_section_header_import': _action_section_header,
    'p_annots_single': _action_annots_single,
    'p_annots_multi': _action_annots_multi,
    'p_annot_obsolete': _action_annot_obsolete,
    'p_annot_todo': _action_annot_todo,

    # -- Section Body --
    'p_section_body_class': _action_section_body,
    'p_section_body_func': _action_section_body,
    'p_section_body_import': _action_section_body,
    'p_import_block_single': _action_import_block_single,
    'p_import_block_multi': _action_import_block_multi,
    'p_import_stmt': _action_import_stmt,

    # -- Class Definition --
    'p_class_def': _action_class_def,
    'p_class_body_doc': _action_class_body_doc,
    'p_class_body_nodoc': _action_class_body_nodoc,
    'p_name_list_single': _action_name_list_single,
    'p_name_list_multi': _action_name_list_multi,

    # -- Tier 3: Artifact Members --
    'p_member_list': _collect_list,
    'p_member_list_empty': _empty_list,
    'p_member': _action_member,
    'p_member_annotated': _action_member_annotated,
    'p_member_body_attr': _action_member_body,
    'p_member_body_method': _action_member_body,
    'p_attr_decl': _action_attr_decl,

    # -- Method Definition --
    'p_method_def': _action_method_def,
    'p_method_def_decorated': _action_method_def_decorated,
    'p_method_name_id': _action_method_name,
    'p_method_name_init': _action_method_name,
    'p_param_tail': _action_param_tail,
    'p_param_tail_empty': _action_param_tail_empty,
    'p_ret_annot': _action_ret_annot,
    'p_ret_annot_empty': _action_ret_annot_empty,
    'p_decorator': _action_decorator,

    # -- Function Definition --
    'p_func_def': _action_func_def,
    'p_func_def_decorated': _action_func_def_decorated,
    'p_param_body': _action_param_body,
    'p_param_body_empty': _action_param_body_empty,

    # -- Body / Snippets --
    'p_body_doc': _action_body_doc,
    'p_body_nodoc': _action_body_nodoc,
    'p_snippet_list': _collect_list,
    'p_snippet_list_empty': _empty_list,
    'p_snippet_comment': _action_snippet_comment,
    'p_snippet_nocomment': _action_snippet_nocomment,
    'p_stmt_list': _collect_list,
    'p_stmt_list_empty': _empty_list,
    'p_stmt_simple': _action_stmt_simple,
    'p_stmt_compound': _action_stmt_compound,

    # -- Token Sequence --
    'p_token_seq_single': _action_token_seq_single,
    'p_token_seq_multi': _action_token_seq_multi,
    'p_token_item_token': _action_token_item,
    'p_token_item_enclosed': _action_token_item,
    'p_enclosed_paren': _action_enclosed,
    'p_enclosed_brack': _action_enclosed,
    'p_enclosed_brace': _action_enclosed,
    'p_inner': _action_inner,
    'p_inner_empty': _action_inner_empty,
    'p_inner_item_token': _action_inner_item,
    'p_inner_item_newline': _action_inner_item,

    # -- Token Catch-All --
    'p_token': _action_token,
}
