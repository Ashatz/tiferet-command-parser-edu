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

# *** helpers

# ** helper: build_module
def build_module(groups, docstring=None):
    '''
    Build a Module AST node from a list of groups.

    :param groups: The list of Group nodes.
    :type groups: list
    :param docstring: Optional module-level docstring text.
    :type docstring: str | None
    :return: A Module AST node.
    :rtype: dict
    '''

    return {'type': 'Module', 'groups': groups, 'docstring': docstring}

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
