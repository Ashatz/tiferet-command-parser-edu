"""Parser Grammar Assets"""

# *** imports

# ** app
from . import lexer as _lexer

# *** constants

# ** constant: tokens (re-export from lexer)
TOKENS = _lexer.TOKENS

# ** constant: precedence
precedence = (
    ('right', 'COLON'),
    ('right', 'ARROW'),
    ('nonassoc', 'ARTIFACT_START', 'ARTIFACT_SECTION', 'ARTIFACT_MEMBER',
                 'OBSOLETE', 'TODO', 'DEDENT'),
)

# *** grammar

# ** production: tier 1 — module / artifact groups (rules 1–6)

# * rule: module (rule 1)
# Module --> GroupList
p_module = 'module : group_list'

# * rule: group_list (rules 2–3, PLY adapted: empty base case)
# GroupList --> GroupList Group | ε
p_group_list = 'group_list : group_list group'
p_group_list_empty = 'group_list : '

# * rule: group (rule 4)
# Group --> GroupHeader NEWLINE SectionList
p_group = 'group : group_header NEWLINE section_list'

# * rule: group_header (rules 5–6)
# GroupHeader --> ARTIFACT_IMPORTS_START | ARTIFACT_START
p_group_header_imports = 'group_header : ARTIFACT_IMPORTS_START'
p_group_header_start = 'group_header : ARTIFACT_START'

# ** production: tier 2 — artifact sections (rules 7–16)

# * rule: section_list (rules 7–8, PLY adapted: empty base case)
# SectionList --> SectionList Section | ε
p_section_list = 'section_list : section_list section'
p_section_list_empty = 'section_list : '

# * rule: section (rules 9–11)
# Section --> SectionHeader NEWLINE SectionBody
# Section --> Annots SectionHeader NEWLINE SectionBody
# Section --> SectionHeader NEWLINE Annots SectionBody
p_section = 'section : section_header NEWLINE section_body'
p_section_annotated = 'section : annots section_header NEWLINE section_body'
p_section_post_annotated = 'section : section_header NEWLINE annots section_body'

# * rule: section_header (rules 11–12)
# SectionHeader --> ARTIFACT_SECTION | ARTIFACT_IMPORT_GROUP
p_section_header_section = 'section_header : ARTIFACT_SECTION'
p_section_header_import = 'section_header : ARTIFACT_IMPORT_GROUP'

# * rule: annots (rules 13–14)
# Annots --> Annot | Annots Annot
p_annots_single = 'annots : annot'
p_annots_multi = 'annots : annots annot'

# * rule: annot (rules 15–16)
# Annot --> OBSOLETE NEWLINE | TODO NEWLINE
p_annot_obsolete = 'annot : OBSOLETE NEWLINE'
p_annot_todo = 'annot : TODO NEWLINE'

# ** production: section body (rules 17–22)

# * rule: section_body (rules 17–19)
# SectionBody --> ClassDef | FuncDef | ImportBlock
p_section_body_class = 'section_body : class_def'
p_section_body_func = 'section_body : func_def'
p_section_body_import = 'section_body : import_block'

# * rule: import_block (rules 20–21)
# ImportBlock --> ImportStmt | ImportBlock ImportStmt
p_import_block_single = 'import_block : import_stmt'
p_import_block_multi = 'import_block : import_block import_stmt'

# * rule: import_stmt (rule 22)
# ImportStmt --> PYTHON_KEYWORD TokenSeq NEWLINE
p_import_stmt = 'import_stmt : PYTHON_KEYWORD token_seq NEWLINE'

# ** production: class definition (rules 23–27)

# * rule: class_def (rule 23)
# ClassDef --> CLASS IDENTIFIER LPAREN NameList RPAREN COLON NEWLINE INDENT ClassBody DEDENT
p_class_def = 'class_def : CLASS IDENTIFIER LPAREN name_list RPAREN COLON NEWLINE INDENT class_body DEDENT'

# * rule: class_body (rules 24–25)
# ClassBody --> DOCSTRING NEWLINE MemberList | MemberList
p_class_body_doc = 'class_body : DOCSTRING NEWLINE member_list'
p_class_body_nodoc = 'class_body : member_list'

# * rule: name_list (rules 26–27)
# NameList --> IDENTIFIER | NameList COMMA IDENTIFIER
p_name_list_single = 'name_list : IDENTIFIER'
p_name_list_multi = 'name_list : name_list COMMA IDENTIFIER'

# ** production: tier 3 — artifact members (rules 28–34)

# * rule: member_list (rules 28–29, PLY adapted: empty base case)
# MemberList --> MemberList Member | ε
p_member_list = 'member_list : member_list member'
p_member_list_empty = 'member_list : '

# * rule: member (rules 30–32)
# Member --> ARTIFACT_MEMBER NEWLINE MemberBody
# Member --> Annots ARTIFACT_MEMBER NEWLINE MemberBody
# Member --> ARTIFACT_MEMBER NEWLINE Annots MemberBody
p_member = 'member : ARTIFACT_MEMBER NEWLINE member_body'
p_member_annotated = 'member : annots ARTIFACT_MEMBER NEWLINE member_body'
p_member_post_annotated = 'member : ARTIFACT_MEMBER NEWLINE annots member_body'

# * rule: member_body (rules 32–33)
# MemberBody --> AttrDecl | MethodDef
p_member_body_attr = 'member_body : attr_decl'
p_member_body_method = 'member_body : method_def'

# * rule: attr_decl (rule 34)
# AttrDecl --> IDENTIFIER COLON TokenSeq NEWLINE
p_attr_decl = 'attr_decl : IDENTIFIER COLON token_seq NEWLINE'

# ** production: method definition (rules 35–43)

# * rule: method_def (rules 35–36)
# MethodDef --> DEF MethodName LPAREN SELF ParamTail RPAREN RetAnnot COLON NEWLINE INDENT Body DEDENT
# MethodDef --> Decorator DEF MethodName LPAREN SELF ParamTail RPAREN RetAnnot COLON NEWLINE INDENT Body DEDENT
p_method_def = 'method_def : DEF method_name LPAREN SELF param_tail RPAREN ret_annot COLON NEWLINE INDENT body DEDENT'
p_method_def_decorated = 'method_def : decorator DEF method_name LPAREN SELF param_tail RPAREN ret_annot COLON NEWLINE INDENT body DEDENT'

# * rule: method_name (rules 37–38)
# MethodName --> IDENTIFIER | INIT
p_method_name_id = 'method_name : IDENTIFIER'
p_method_name_init = 'method_name : INIT'

# * rule: param_tail (rules 39–40)
# ParamTail --> COMMA TokenSeq | ε
p_param_tail = 'param_tail : COMMA token_seq'
p_param_tail_empty = 'param_tail : '

# * rule: ret_annot (rules 41–42)
# RetAnnot --> ARROW TokenSeq | ε
p_ret_annot = 'ret_annot : ARROW token_seq'
p_ret_annot_empty = 'ret_annot : '

# * rule: decorator (rule 43)
# Decorator --> AT TokenSeq NEWLINE
p_decorator = 'decorator : AT token_seq NEWLINE'

# ** production: function definition (rules 44–47)

# * rule: func_def (rules 44–45)
# FuncDef --> DEF IDENTIFIER LPAREN ParamBody RPAREN RetAnnot COLON NEWLINE INDENT Body DEDENT
# FuncDef --> Decorator DEF IDENTIFIER LPAREN ParamBody RPAREN RetAnnot COLON NEWLINE INDENT Body DEDENT
p_func_def = 'func_def : DEF IDENTIFIER LPAREN param_body RPAREN ret_annot COLON NEWLINE INDENT body DEDENT'
p_func_def_decorated = 'func_def : decorator DEF IDENTIFIER LPAREN param_body RPAREN ret_annot COLON NEWLINE INDENT body DEDENT'

# * rule: param_body (rules 46–47)
# ParamBody --> TokenSeq | ε
p_param_body = 'param_body : token_seq'
p_param_body_empty = 'param_body : '

# ** production: method / function body — snippets (rules 48–57)

# * rule: body (rules 48–49)
# Body --> DOCSTRING NEWLINE SnippetList | SnippetList
p_body_doc = 'body : DOCSTRING NEWLINE snippet_list'
p_body_nodoc = 'body : snippet_list'

# * rule: snippet_list (rules 50–51, PLY adapted: empty base case)
# SnippetList --> SnippetList Snippet | ε
p_snippet_list = 'snippet_list : snippet_list snippet'
p_snippet_list_empty = 'snippet_list : '

# * rule: snippet (rules 52–53)
# Snippet --> LINE_COMMENT NEWLINE StmtList | StmtList
p_snippet_comment = 'snippet : LINE_COMMENT NEWLINE stmt_list'
p_snippet_nocomment = 'snippet : stmt_list'

# * rule: stmt_list (rules 54–55, PLY adapted: empty base case)
# StmtList --> StmtList Stmt | ε
p_stmt_list = 'stmt_list : stmt_list stmt'
p_stmt_list_empty = 'stmt_list : '

# * rule: stmt (rules 56–57)
# Stmt --> TokenSeq NEWLINE
# Stmt --> TokenSeq NEWLINE INDENT StmtList DEDENT
p_stmt_simple = 'stmt : token_seq NEWLINE'
p_stmt_compound = 'stmt : token_seq NEWLINE INDENT stmt_list DEDENT'

# ** production: token sequence — generic content (rules 58–68)

# * rule: token_seq (rules 58–59)
# TokenSeq --> TokenItem | TokenSeq TokenItem
p_token_seq_single = 'token_seq : token_item'
p_token_seq_multi = 'token_seq : token_seq token_item'

# * rule: token_item (rules 60–61)
# TokenItem --> Token | Enclosed
p_token_item_token = 'token_item : token'
p_token_item_enclosed = 'token_item : enclosed'

# * rule: enclosed (rules 62–64)
# Enclosed --> LPAREN Inner RPAREN | LBRACK Inner RBRACK | LBRACE Inner RBRACE
p_enclosed_paren = 'enclosed : LPAREN inner RPAREN'
p_enclosed_brack = 'enclosed : LBRACK inner RBRACK'
p_enclosed_brace = 'enclosed : LBRACE inner RBRACE'

# * rule: inner (rules 65–66, adapted to left-recursion for PLY)
# Inner --> Inner InnerItem | ε
p_inner = 'inner : inner inner_item'
p_inner_empty = 'inner : '

# * rule: inner_item (rules 67–68)
# InnerItem --> TokenItem | NEWLINE
p_inner_item_token = 'inner_item : token_item'
p_inner_item_newline = 'inner_item : NEWLINE'

# ** production: token — content terminals (rule 69)

# * rule: token
# Token catches all content terminals except structural delimiters
# (NEWLINE, INDENT, DEDENT, brackets, artifact markers, OBSOLETE, TODO, LINE_COMMENT).
p_token = '''token : IDENTIFIER
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

# ** constant: rules
RULES = {
    # -- Tier 1: Module / Artifact Groups (rules 1–6) --
    'p_module': p_module,
    'p_group_list': p_group_list,
    'p_group_list_empty': p_group_list_empty,
    'p_group': p_group,
    'p_group_header_imports': p_group_header_imports,
    'p_group_header_start': p_group_header_start,

    # -- Tier 2: Artifact Sections (rules 7–16) --
    'p_section_list': p_section_list,
    'p_section_list_empty': p_section_list_empty,
    'p_section': p_section,
    'p_section_annotated': p_section_annotated,
    'p_section_post_annotated': p_section_post_annotated,
    'p_section_header_section': p_section_header_section,
    'p_section_header_import': p_section_header_import,
    'p_annots_single': p_annots_single,
    'p_annots_multi': p_annots_multi,
    'p_annot_obsolete': p_annot_obsolete,
    'p_annot_todo': p_annot_todo,

    # -- Section Body (rules 17–22) --
    'p_section_body_class': p_section_body_class,
    'p_section_body_func': p_section_body_func,
    'p_section_body_import': p_section_body_import,
    'p_import_block_single': p_import_block_single,
    'p_import_block_multi': p_import_block_multi,
    'p_import_stmt': p_import_stmt,

    # -- Class Definition (rules 23–27) --
    'p_class_def': p_class_def,
    'p_class_body_doc': p_class_body_doc,
    'p_class_body_nodoc': p_class_body_nodoc,
    'p_name_list_single': p_name_list_single,
    'p_name_list_multi': p_name_list_multi,

    # -- Tier 3: Artifact Members (rules 28–34) --
    'p_member_list': p_member_list,
    'p_member_list_empty': p_member_list_empty,
    'p_member': p_member,
    'p_member_annotated': p_member_annotated,
    'p_member_post_annotated': p_member_post_annotated,
    'p_member_body_attr': p_member_body_attr,
    'p_member_body_method': p_member_body_method,
    'p_attr_decl': p_attr_decl,

    # -- Method Definition (rules 35–43) --
    'p_method_def': p_method_def,
    'p_method_def_decorated': p_method_def_decorated,
    'p_method_name_id': p_method_name_id,
    'p_method_name_init': p_method_name_init,
    'p_param_tail': p_param_tail,
    'p_param_tail_empty': p_param_tail_empty,
    'p_ret_annot': p_ret_annot,
    'p_ret_annot_empty': p_ret_annot_empty,
    'p_decorator': p_decorator,

    # -- Function Definition (rules 44–47) --
    'p_func_def': p_func_def,
    'p_func_def_decorated': p_func_def_decorated,
    'p_param_body': p_param_body,
    'p_param_body_empty': p_param_body_empty,

    # -- Body / Snippets (rules 48–57) --
    'p_body_doc': p_body_doc,
    'p_body_nodoc': p_body_nodoc,
    'p_snippet_list': p_snippet_list,
    'p_snippet_list_empty': p_snippet_list_empty,
    'p_snippet_comment': p_snippet_comment,
    'p_snippet_nocomment': p_snippet_nocomment,
    'p_stmt_list': p_stmt_list,
    'p_stmt_list_empty': p_stmt_list_empty,
    'p_stmt_simple': p_stmt_simple,
    'p_stmt_compound': p_stmt_compound,

    # -- Token Sequence (rules 58–68) --
    'p_token_seq_single': p_token_seq_single,
    'p_token_seq_multi': p_token_seq_multi,
    'p_token_item_token': p_token_item_token,
    'p_token_item_enclosed': p_token_item_enclosed,
    'p_enclosed_paren': p_enclosed_paren,
    'p_enclosed_brack': p_enclosed_brack,
    'p_enclosed_brace': p_enclosed_brace,
    'p_inner': p_inner,
    'p_inner_empty': p_inner_empty,
    'p_inner_item_token': p_inner_item_token,
    'p_inner_item_newline': p_inner_item_newline,

    # -- Token Catch-All (rule 69) --
    'p_token': p_token,
}

# *** helpers

# ** helper: build_module
def build_module(groups):
    '''
    Build a Module AST node from a list of groups.

    :param groups: The list of Group nodes.
    :type groups: list
    :return: A Module AST node.
    :rtype: dict
    '''

    return {'type': 'Module', 'groups': groups}

# ** helper: build_group
def build_group(header, sections):
    '''
    Build a Group AST node.

    :param header: The group header token value.
    :type header: str
    :param sections: The list of Section nodes.
    :type sections: list
    :return: A Group AST node.
    :rtype: dict
    '''

    return {'type': 'Group', 'header': header, 'sections': sections}

# ** helper: build_section
def build_section(header, body, annotations=None):
    '''
    Build a Section AST node.

    :param header: The section header token value.
    :type header: str
    :param body: The section body node (ClassDef, FuncDef, or ImportBlock).
    :type body: dict
    :param annotations: Optional list of annotation strings.
    :type annotations: list | None
    :return: A Section AST node.
    :rtype: dict
    '''

    return {
        'type': 'Section',
        'header': header,
        'annotations': annotations or [],
        'body': body,
    }

# ** helper: build_annot
def build_annot(kind, text):
    '''
    Build an Annot AST node.

    :param kind: The annotation kind (OBSOLETE or TODO).
    :type kind: str
    :param text: The annotation token value.
    :type text: str
    :return: An Annot AST node.
    :rtype: dict
    '''

    return {'type': 'Annot', 'kind': kind, 'text': text}

# ** helper: build_class_def
def build_class_def(name, bases, body, docstring=None):
    '''
    Build a ClassDef AST node.

    :param name: The class name.
    :type name: str
    :param bases: The list of base class names.
    :type bases: list
    :param body: The list of Member nodes.
    :type body: list
    :param docstring: Optional docstring text.
    :type docstring: str | None
    :return: A ClassDef AST node.
    :rtype: dict
    '''

    return {
        'type': 'ClassDef',
        'name': name,
        'bases': bases,
        'docstring': docstring,
        'members': body,
    }

# ** helper: build_member
def build_member(kind, body, annotations=None):
    '''
    Build a Member AST node.

    :param kind: The member kind (attribute, method, or init).
    :type kind: str
    :param body: The member body node (AttrDecl or MethodDef).
    :type body: dict
    :param annotations: Optional list of annotation nodes.
    :type annotations: list | None
    :return: A Member AST node.
    :rtype: dict
    '''

    return {
        'type': 'Member',
        'kind': kind,
        'annotations': annotations or [],
        'body': body,
    }

# ** helper: build_attr_decl
def build_attr_decl(name, type_annotation):
    '''
    Build an AttrDecl AST node.

    :param name: The attribute name.
    :type name: str
    :param type_annotation: The type annotation token sequence.
    :type type_annotation: list
    :return: An AttrDecl AST node.
    :rtype: dict
    '''

    return {'type': 'AttrDecl', 'name': name, 'type_annotation': type_annotation}

# ** helper: build_method_def
def build_method_def(name, params, body, return_type=None, decorator=None, docstring=None):
    '''
    Build a MethodDef AST node.

    :param name: The method name.
    :type name: str
    :param params: The parameter token sequence (after SELF).
    :type params: list
    :param body: The list of Snippet nodes.
    :type body: list
    :param return_type: Optional return type annotation tokens.
    :type return_type: list | None
    :param decorator: Optional decorator token sequence.
    :type decorator: list | None
    :param docstring: Optional docstring text.
    :type docstring: str | None
    :return: A MethodDef AST node.
    :rtype: dict
    '''

    return {
        'type': 'MethodDef',
        'name': name,
        'params': params,
        'return_type': return_type,
        'decorator': decorator,
        'docstring': docstring,
        'body': body,
    }

# ** helper: build_func_def
def build_func_def(name, params, body, return_type=None, decorator=None, docstring=None):
    '''
    Build a FuncDef AST node.

    :param name: The function name.
    :type name: str
    :param params: The parameter token sequence.
    :type params: list
    :param body: The list of Snippet nodes.
    :type body: list
    :param return_type: Optional return type annotation tokens.
    :type return_type: list | None
    :param decorator: Optional decorator token sequence.
    :type decorator: list | None
    :param docstring: Optional docstring text.
    :type docstring: str | None
    :return: A FuncDef AST node.
    :rtype: dict
    '''

    return {
        'type': 'FuncDef',
        'name': name,
        'params': params,
        'return_type': return_type,
        'decorator': decorator,
        'docstring': docstring,
        'body': body,
    }

# ** helper: build_decorator
def build_decorator(tokens):
    '''
    Build a Decorator AST node.

    :param tokens: The decorator token sequence (after AT).
    :type tokens: list
    :return: A Decorator AST node.
    :rtype: dict
    '''

    return {'type': 'Decorator', 'tokens': tokens}

# ** helper: build_body
def build_body(snippets, docstring=None):
    '''
    Build a Body AST node for a method or function interior.

    :param snippets: The list of Snippet nodes.
    :type snippets: list
    :param docstring: Optional docstring text.
    :type docstring: str | None
    :return: A Body AST node.
    :rtype: dict
    '''

    return {'type': 'Body', 'docstring': docstring, 'snippets': snippets}

# ** helper: build_snippet
def build_snippet(statements, comment=None):
    '''
    Build a Snippet AST node.

    :param statements: The list of Stmt nodes.
    :type statements: list
    :param comment: Optional LINE_COMMENT header text.
    :type comment: str | None
    :return: A Snippet AST node.
    :rtype: dict
    '''

    return {'type': 'Snippet', 'comment': comment, 'statements': statements}

# ** helper: build_stmt
def build_stmt(tokens, block=None):
    '''
    Build a Stmt AST node.

    :param tokens: The statement token sequence.
    :type tokens: list
    :param block: Optional indented sub-block (for compound statements).
    :type block: list | None
    :return: A Stmt AST node.
    :rtype: dict
    '''

    return {'type': 'Stmt', 'tokens': tokens, 'block': block}

# ** helper: build_import_stmt
def build_import_stmt(keyword, tokens):
    '''
    Build an ImportStmt AST node.

    :param keyword: The leading keyword (import or from).
    :type keyword: str
    :param tokens: The token sequence following the keyword.
    :type tokens: list
    :return: An ImportStmt AST node.
    :rtype: dict
    '''

    return {'type': 'ImportStmt', 'keyword': keyword, 'tokens': tokens}

# ** helper: build_token_seq
def build_token_seq(items):
    '''
    Build a flat list from token sequence items.

    :param items: The list of token items.
    :type items: list
    :return: The flattened token sequence.
    :rtype: list
    '''

    return items

# ** helper: build_enclosed
def build_enclosed(open_bracket, items, close_bracket):
    '''
    Build an Enclosed AST node for a matched bracket group.

    :param open_bracket: The opening bracket token.
    :type open_bracket: str
    :param items: The inner items.
    :type items: list
    :param close_bracket: The closing bracket token.
    :type close_bracket: str
    :return: An Enclosed AST node.
    :rtype: dict
    '''

    return {
        'type': 'Enclosed',
        'open': open_bracket,
        'items': items,
        'close': close_bracket,
    }
