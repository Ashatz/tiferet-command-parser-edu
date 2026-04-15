"""Scanner Parser Utility"""

# *** imports

# ** core
from typing import List, Dict, Any, Optional

# ** infra
import ply.yacc as yacc

# ** app
from ..events import a
from ..interfaces import ParserService
from ..mappers import TokenAggregate, Decl, Stmt, Expr, Type, ParamList
from ..mappers.ast import TypeKind

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
    
    # * method: parse_artifact_header (helper)
    @staticmethod
    def parse_artifact_header(token_value: str) -> tuple:
        '''
        Parse an artifact header token value into a (name, type) tuple.

        For colon-separated headers (e.g. "# ** event: ping"),
        the name is the part after the colon and the type combines the
        marker with the kind (e.g. "** event").

        For simple headers (e.g. "# *** imports", "# ** app"),
        the name is the trailing word and the type is the marker.

        :param token_value: The raw artifact token value.
        :type token_value: str
        :return: A (name, type) tuple.
        :rtype: tuple
        '''

        # Strip leading # and whitespace, then split marker from rest.
        stripped = token_value.lstrip('#').strip()
        parts = stripped.split(None, 1)
        if len(parts) < 2:
            return (parts[0] if parts else 'unknown', '')

        # Extract the marker and the remainder.
        marker = parts[0]
        rest = parts[1]

        # Check for colon-separated pattern (e.g. "event: ping").
        if ':' in rest:
            kind, _, name = rest.partition(':')
            return (name.strip(), f'{marker} {kind.strip()}')

        # Simple header (e.g. "imports", "app").
        return (rest.strip(), marker)

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
    
    # * method: get_attribute_type (helper)
    @staticmethod
    def get_attribute_type(type_str: str, additional_types: Optional[Type] = None) -> Type:
        
        if type_str == 'int':
            return Type.new(TypeKind.INT)
        elif type_str == 'str':
            return Type.new(TypeKind.STR)
        elif type_str == 'float':
            return Type.new(TypeKind.FLOAT)
        elif type_str == 'bool':
            return Type.new(TypeKind.BOOL)
        elif type_str == 'list':
            return Type.new(TypeKind.LIST)
        elif type_str == 'dict':
            return Type.new(TypeKind.DICT)
        else:
            return Type.new_class_type(subclasses=additional_types)


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

    # -- Tier 1: Module & Artifact Groups --

    # * method: p_module (rule)
    def p_module(self, p):
        '''module : group_list'''

        # Build Module AST node from group list.
        p[0] = Decl.new_module_decl(name='__main__', code=p[1])

    # * method: p_module_doc (rule)
    def p_module_doc(self, p):
        '''module : DOCSTRING NEWLINE module'''

        # Set the module docstring and pass through the module body.
        p[3].set_doc_string(p[1])
        p[0] = p[3]

    # * method: p_group_list (rule)
    def p_group_list(self, p):
        '''group_list : group_list group'''

        # Collect groups into a list via left-recursive accumulation.
        if p[1]:
            p[1].set_next(p[2])
            p[0] = p[1]
        else:
            p[0] = p[2]

    # * method: p_group_list_empty (rule)
    def p_group_list_empty(self, p):
        '''group_list : '''

        # Initialize an empty group list.
        p[0] = None

    # * method: p_group (rule)
    def p_group(self, p):
        '''group : group_header NEWLINE section_list'''

        # Build Group AST node: header NEWLINE section_list.
        p[0] = Stmt.new_artifact_stmt(p[1], p[3])

    # * method: p_group_header_imports (rule)
    def p_group_header_imports(self, p):
        '''group_header : ARTIFACT_IMPORTS_START'''

        # Parse the group header token value via helper.
        name, type = self.parse_artifact_header(p[1])
        p[0] = Decl.new_artifact_decl(name, type)

    # * method: p_group_header_start (rule)
    def p_group_header_start(self, p):
        '''group_header : ARTIFACT_START'''

        # Parse the group header token value via helper.
        name, type = self.parse_artifact_header(p[1])
        p[0] = Decl.new_artifact_decl(name, type)

    # -- Tier 2: Artifact Sections & Annotations --

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
        p[0] = None

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

        # Parse the section header token value via helper.
        name, type = self.parse_artifact_header(p[1])
        p[0] = Decl.new_artifact_decl(name, type)

    # * method: p_section_header_import (rule)
    def p_section_header_import(self, p):
        '''section_header : ARTIFACT_IMPORT_GROUP'''

        # Parse the section header token value via helper.
        name, type = self.parse_artifact_header(p[1])
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
        p[0] = Stmt.new_decl_stmt(p[1])

    # * method: p_section_body_import (rule)
    def p_section_body_import(self, p):
        '''section_body : import_block'''

        # Pass through the section body.
        p[0] = p[1]

    # -- Import Statements --

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

    # * method: p_from_expr_dot_middle (rule)
    def p_from_expr_dot_middle(self, p):
        '''from_expr : from_expr DOT IDENTIFIER'''

        # Build FromExpr with dot notation and additional identifier.
        p[1].name += '.' + p[3]
        p[0] = p[1]

    # -- Class Definitions --

    # * method: p_class_def (rule)
    def p_class_def(self, p):
        '''class_def : CLASS IDENTIFIER LPAREN super_cls_list RPAREN COLON NEWLINE INDENT class_body DEDENT'''

        # Build ClassDef AST node.
        p[0] = Decl.new_class_decl(
            name=p[2],
            subclasses=p[4],
            doc_string=p[9].get('docstring', None),
            members=Stmt.new_decl_stmt(p[9].get('members', None))
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

    # * method: p_super_cls_list_empty (rule)
    def p_super_cls_list_empty(self, p):
        '''super_cls_list : '''

        # Initialize an empty super class list.
        p[0] = None

    # * method: p_super_cls_list_single (rule)
    def p_super_cls_list_single(self, p):
        '''super_cls_list : super_cls'''

        # Start a super class list with a single class.
        p[0] = p[1]

    # * method: p_super_cls_multi (rule)
    def p_super_cls_multi(self, p):
        '''super_cls : super_cls COMMA super_cls'''

        # Add the subtype to the super class list.
        p[1].set_subtype(p[3])
        p[0] = p[1]

    # * method: p_super_cls (rule)
    def p_super_cls(self, p):
        '''super_cls : IDENTIFIER'''

        # Start a super class list with a single identifier.
        p[0] = Type.new_class_type(name=p[1])

    # -- Tier 3: Artifact Members --

    # * method: p_member_list (rule)
    def p_member_list(self, p):
        '''member_list : member_list member'''

        # Collect members via linked-list accumulation.
        if p[1]:
            p[1].set_next(p[2])
        p[0] = p[1]

    # * method: p_member_list_single (rule)
    def p_member_list_single(self, p):
        '''member_list : member'''

        # Start a member list with a single member.
        p[0] = p[1]

    # * method: p_member_list_empty (rule)
    def p_member_list_empty(self, p):
        '''member_list : '''

        # Initialize an empty member list.
        p[0] = None

    # * method: p_member_decl (rule)
    def p_member_decl(self, p):
        '''member : ARTIFACT_MEMBER NEWLINE member_stmt'''

        # Build Member AST node.
        kind = self.parse_member_kind(p[1])
        p[0] = Decl.new_member_decl(kind, p[3])

    # * method: p_member_annotated (rule)
    def p_member_annotated(self, p):
        '''member : annots ARTIFACT_MEMBER NEWLINE member_stmt'''

        # Build Member AST node with annotations.
        kind = self.parse_member_kind(p[2])
        p[0] = Decl.new_member_decl(kind, p[4], annots=p[1])

    # * method: p_member_post_annotated (rule)
    def p_member_post_annotated(self, p):
        '''member : ARTIFACT_MEMBER NEWLINE annots member_stmt'''

        # Build Member AST node with post-header annotations.
        kind = self.parse_member_kind(p[1])
        p[0] = Decl.new_member_decl(kind, p[4], annots=p[3])

    # * method: p_member_attr_stmt (rule)
    def p_member_attr_stmt(self, p):
        '''member_stmt : attr_decl'''

        # Create an attribute member statement from the attribute declaration.
        p[0] = Stmt.new_decl_stmt(p[1])

    # * method: p_member_body_method (rule)
    def p_member_body_method(self, p):
        '''member_stmt : method_decl'''

        # Create a method member statement from the method declaration.
        p[0] = Stmt.new_decl_stmt(p[1])

    # * method: p_member_stmt_method_decorated (rule)
    def p_member_stmt_method_decorated(self, p):
        '''member_stmt : decorator_stmt NEWLINE member_stmt'''

        # Build decorated member statement node.
        p[1].set_next(p[3])
        p[0] = p[1]

    # -- Attribute Declarations --

    # * method: p_attr_decl (rule)
    def p_attr_decl(self, p):
        '''attr_decl : IDENTIFIER NEWLINE'''

        # Build AttrDecl AST node.
        p[0] = Decl.new_attr_decl(name=p[1])

    # * method: p_attr_decl_type (rule)
    def p_attr_decl_type(self, p):
        '''attr_decl : IDENTIFIER COLON attr_types NEWLINE'''

        # Build AttrDecl AST node with type annotation.
        p[0] = Decl.new_attr_decl(name=p[1], types=p[3])

    # * method: p_attr_types_single (rule)
    def p_attr_types_single(self, p):
        '''attr_types : IDENTIFIER'''

        # Build a single type annotation for the attribute.
        p[0] = self.get_attribute_type(p[1])

    # * method: p_attr_types_multi (rule)
    def p_attr_types_multi(self, p):
        '''attr_types : attr_types PIPE IDENTIFIER'''

        # Build multiple type annotations for the attribute.
        p[1].set_subtype(self.get_attribute_type(p[3]))
        p[0] = p[1]

    # -- Decorators --

    # * method: p_decorator_stmt (rule)
    def p_decorator_stmt(self, p):
        '''decorator_stmt : AT decorator_call NEWLINE'''

        # Build Decorator AST node.
        p[0] = Stmt.new_expr_stmt(p[2])

    # * method: p_decorator_call (rule)
    def p_decorator_call(self, p):
        '''decorator_call : decorator_ident LPAREN decorator_args RPAREN'''

        # Build Decorator call node.
        p[0] = Expr.new_call_expr(p[1], p[3])

    # * method: p_decorator_ident (rule)
    def p_decorator_ident(self, p):
        '''decorator_ident : IDENTIFIER'''

        # Pass through decorator identifier.
        p[0] = Expr.new_name_expr(p[1])

    # * method: p_decorator_ident_dot (rule)
    def p_decorator_ident_dot(self, p):
        '''decorator_ident : decorator_ident DOT IDENTIFIER'''

        # Build Decorator identifier with dot notation.
        p[0] = Expr.new_name_expr(left=p[1], right=Expr.new_name_expr(name=p[3]))

    # * method: p_decorator_params_single (rule)
    def p_decorator_params_single(self, p):
        '''decorator_args : decorator_arg'''

        # Pass through single decorator parameter sequence.
        p[0] = Expr.new_args_list_expr(p[1])

    # * method: p_decorator_args_multi (rule)
    def p_decorator_args_multi(self, p):
        '''decorator_args : decorator_args COMMA decorator_arg'''

        # Build multiple decorator argument sequence.
        p[0] = Expr.new_args_list_expr(p[1], p[3])

    # * method: p_decorator_arg_literal (rule)
    def p_decorator_arg_literal(self, p):
        '''decorator_arg : name_or_literal_expr'''

        # Pass through the resolved name or literal expression.
        p[0] = p[1]

    # -- Method Definitions --

    # * method: p_method_decl (rule)
    def p_method_decl(self, p):
        '''method_decl : DEF method_name method_type COLON NEWLINE INDENT method_doc_string snippet_list DEDENT'''

        # Build MethodDecl AST node.
        p[0] = Decl.new_func_decl(
             name=p[2],
             type=p[3],
             doc_string=p[7],
             body=p[8]
        )

    # * method: p_method_name (rule)
    def p_method_name(self, p):
        '''method_name : IDENTIFIER 
                    | INIT'''

        # Pass through the method name identifier.
        p[0] = p[1]

    # * method: p_method_type (rule)
    def p_method_type(self, p):
        '''method_type : LPAREN method_param_list RPAREN ret_annot'''

        # Build a method type annotation from the parameter list and return type annotation.
        p[0] = Type.new_func_type(params=p[2], return_type=p[4])

    # * method: p_method_doc_string (rule)
    def p_method_doc_string(self, p):
        '''method_doc_string : DOCSTRING NEWLINE'''

        # Pass through the method docstring.
        p[0] = p[1]

    # * method: p_method_doc_string_empty (rule)
    def p_method_doc_string_empty(self, p):
        '''method_doc_string : '''

        # Build empty method docstring.
        p[0] = None

    # -- Parameters & Type Annotations --

    # * method: p_method_param_list (rule)
    def p_method_param_list(self, p):
        '''method_param_list : SELF COMMA param_list'''

        # Pass through the parameter list, ensuring 'self' is included as the first parameter for method definitions.
        param_list = ParamList.new(name=p[1], type=Type.new_unknown_type())
        param_list.set_next(p[3])
        p[0] = param_list

    # * method: p_method_param_list_self_only (rule)
    def p_method_param_list_self_only(self, p):
        '''method_param_list : SELF'''

        # Build a self-only parameter list for methods that take no additional parameters.
        p[0] = ParamList.new(name=p[1], type=Type.new_unknown_type())

    # * method: p_method_param_list_single (rule)
    def p_method_param_list_single(self, p):
        '''param_list : param'''

        # Start a parameter list with a single parameter.
        p[0] = p[1]

    # * method: p_method_param_list_multi (rule)
    def p_method_param_list_multi(self, p):
        '''param_list : param_list COMMA param'''

        # Extend a parameter list with an additional parameter.
        p[1].set_next(p[3])
        p[0] = p[1]

    # * method: p_method_param (rule)
    def p_method_param(self, p):
        '''param : IDENTIFIER'''

        # Build a single parameter as a name expression.
        p[0] = ParamList.new(name=p[1])

    # * method: p_method_param_args (rule)
    def p_method_param_args(self, p):
        '''param : STAR IDENTIFIER'''

        # Build a single parameter as a *args name expression.
        p[0] = ParamList.new_args_param(name=p[2])

    # * method: p_method_param_kwargs (rule)
    def p_method_param_kwargs(self, p):
        '''param : DOUBLESTAR IDENTIFIER'''

        # Build a single parameter as a **kwargs name expression.
        p[0] = ParamList.new_kwargs_param(name=p[2])

    # * method: p_method_param_type (rule)
    def p_method_param_type(self, p):
        '''param : param COLON param_types'''

        # Build a single parameter with type annotation.
        p[1].set_type(p[3])
        p[0] = p[1]

    # * method: p_param_default (rule)
    def p_param_default(self, p):
        '''param : param EQUALS name_or_literal_expr'''

        # Build a single parameter with default value.
        p[1].set_default(p[3])    
        p[0] = p[1]

    # * method: p_param_newline (rule)
    def p_param_newline(self, p):
        '''param : NEWLINE param'''

        # Pass through a parameter followed by a newline (for multi-line parameter lists).
        p[0] = p[2]

    # * method: p_method_param_types_single (rule)
    def p_method_param_types_single(self, p):
        '''param_types : IDENTIFIER'''

        # Build a single type annotation for the parameter.
        p[0] = self.get_attribute_type(p[1])

    # * method: p_method_param_types_multi (rule)
    def p_method_param_types_multi(self, p):
        '''param_types : param_types PIPE IDENTIFIER'''

        # Build multiple type annotations for the parameter.
        subtype = self.get_attribute_type(p[3])
        p[1].set_subtype(subtype)
        p[0] = p[1]

    # * method: p_ret_annot (rule)
    def p_ret_annot(self, p):
        '''ret_annot : ARROW ret_types'''

        # Build return annotation.
        p[0] = p[2]

    # * method: p_ret_annot_empty (rule)
    def p_ret_annot_empty(self, p):
        '''ret_annot : '''

        # Build empty return annotation.
        p[0] = Type.new_null_type()

    # * method: p_ret_types_single (rule)
    def p_ret_types_single(self, p):
        '''ret_types : IDENTIFIER'''

        # Build a single return type annotation.
        p[0] = self.get_attribute_type(p[1])

    # * method: p_ret_types_multi (rule)
    def p_ret_types_multi(self, p):
        '''ret_types : ret_types PIPE IDENTIFIER'''

        # Build multiple return type annotations.
        ret_type = self.get_attribute_type(p[3])
        p[1].set_return_type(ret_type)
        p[0] = p[1]

    # -- Method Body & Snippets --

    # * method: p_snippet_list (rule)
    def p_snippet_list(self, p):
        '''snippet_list : snippet_list snippet'''

        # Collect snippets into a list via left-recursive accumulation. Otherwise, start a snippet list with the single snippet.
        if p[1]:
            p[1].set_next(p[2])
            p[0] = p[1]
        else:
            p[0] = p[2]

    # * method: p_snippet_list_newline (rule)
    def p_snippet_list_newline(self, p):
        '''snippet_list : snippet_list NEWLINE'''

        # Consume stray NEWLINEs (blank lines) between snippets.
        p[0] = p[1]

    # * method: p_snippet_list_empty (rule)
    def p_snippet_list_empty(self, p):
        '''snippet_list : '''

        # Initialize an empty snippet list.
        p[0] = None

    # * method: p_snippet_comment (rule)
    def p_snippet_comment(self, p):
        '''snippet : comment_list stmt_list'''

        # Build Snippet with comment.
        p[0] = Stmt.new_snippet_stmt(comments=p[1], code=p[2])

    # * method: p_snippet_nocomment (rule)
    def p_snippet_nocomment(self, p):
        '''snippet : stmt_list'''

        # Build Snippet without comment.
        p[0] = Stmt.new_snippet_stmt(code=p[1])

    # * method: p_comment_list_single (rule)
    def p_comment_list_single(self, p):
        '''comment_list : comment_stmt'''

        # Start a comment list with a single comment.
        p[0] = p[1]

    # * method: p_comment_list_multi (rule)
    def p_comment_list_multi(self, p):
        '''comment_list : comment_list comment_stmt'''

        # Extend a comment list with an additional comment.
        p[1].set_next(p[2])
        p[0] = p[1]

    # * method: p_comment_stmt (rule)
    def p_comment_stmt(self, p):
        '''comment_stmt : LINE_COMMENT NEWLINE'''

        # Build Comment AST node.
        expr = Expr.new_comment_expr(p[1])
        p[0] = Stmt.new_comment_stmt(expr)

    # -- Statements --

    # * method: p_stmt_list_single (rule)
    def p_stmt_list_single(self, p):
        '''stmt_list : stmt'''

        # Start a statement list with a single statement.
        p[0] = p[1]

    # * method: p_stmt_list (rule)
    def p_stmt_list(self, p):
        '''stmt_list : stmt_list stmt'''

        # Collect statements into a list via left-recursive accumulation.
        p[1].set_next(p[2])
        p[0] = p[1]

    # * method: p_stmt_list_empty (rule)
    def p_stmt_list_empty(self, p):
        '''stmt_list : '''

        # Initialize an empty statement list.
        p[0] = None

    # * method: p_stmt_return (rule)
    def p_stmt_return(self, p):
        '''stmt : RETURN return_expr NEWLINE'''

        # Build ReturnStmt.
        p[0] = Stmt.new_return_stmt(return_expr=p[2])

    # * method: p_stmt_assign (rule)
    def p_stmt_assign(self, p):
        '''stmt : assign_expr NEWLINE'''

        # Build AssignStmt.
        p[0] = Stmt.new_expr_stmt(p[1])

    # * method: p_stmt_operator (rule)
    def p_stmt_operator(self, p):
        '''stmt : operation_expr NEWLINE'''

        # Build an expression statement for the operator expression.
        p[0] = Stmt.new_expr_stmt(p[1])

    # * method: p_stmt_call (rule)
    def p_stmt_call(self, p):
        '''stmt : call_expr NEWLINE'''

        # Build a call expression statement.
        p[0] = Stmt.new_expr_stmt(p[1])

    # -- Expressions --

    # * method: p_asign_expr (rule)
    def p_assign_expr(self, p):
        '''assign_expr : ident_expr EQUALS name_or_literal_expr'''

        # Build an assignment expression.
        p[0] = Expr.new_assign_expr(target=p[1], value=p[3])

    # * method: p_return_expr (rule)
    def p_return_expr(self, p):
        '''return_expr : name_or_literal_expr
                 | operation_expr
                 | call_expr'''

        # Pass through the return expression.
        p[0] = p[1]

    # * method: p_return_empty_expr (rule)
    def p_return_empty_expr(self, p):
        '''return_expr : '''

        # Build empty return expression.
        p[0] = None

    # * method: p_operation_expr (rule)
    def p_operation_expr(self, p):
        '''operation_expr : name_or_literal_expr operator name_or_literal_expr'''

        # Build a binary operator expression.
        p[0] = Expr.new_operator_expr(left=p[1], operator=p[2], right=p[3])

    # * method: p_call_expr (rule)
    def p_call_expr(self, p):
        '''call_expr : ident_expr LPAREN call_args RPAREN'''

        # Build a call expression.
        p[0] = Expr.new_call_expr(p[1], p[3])

    # * method: p_call_args_single (rule)
    def p_call_args_single(self, p):
        '''call_args : call_arg'''

        # Build a single call argument as an argument list with one element.
        p[0] = Expr.new_args_list_expr(p[1])

    # * method: p_call_args_multi (rule)
    def p_call_args_multi(self, p):
        '''call_args : call_args COMMA call_arg'''

        # Build multiple call arguments into an argument list.
        p[0] = Expr.new_args_list_expr(p[1], p[3])

    # * method: p_call_arg (rule)
    def p_call_arg(self, p):
        '''call_arg : name_or_literal_expr'''

        # Pass through a call argument as a name or literal expression.
        p[0] = p[1]

    # * method: p_literal_expr (rule)
    def p_literal_expr(self, p):
        '''literal_expr : STRING_LITERAL
                 | NUMBER_LITERAL
                 | TRUE
                 | FALSE'''

        # Build a literal expression from a string, number, or boolean token.
        p[0] = Expr.new_name_or_literal_expr(p[1])

    # * method: p_name_or_literal_expr (rule)
    def p_name_or_literal_expr(self, p):
        '''name_or_literal_expr : ident_expr
                 | literal_expr'''

        # Pass through the resolved identity or literal expression.
        p[0] = p[1]

    # * method: p_ident_expr (rule)
    def p_ident_expr(self, p):
        '''ident_expr : ident
                 | ident_dot'''

        # Build an identifier expression from either a simple identifier or a dotted identifier.
        p[0] = Expr.new_name_expr(p[1])

    # -- Code Elements & Structures --

    # * method: p_ident (rule)
    def p_ident(self, p):
        '''ident : IDENTIFIER
                | SELF'''

        # Pass through an identifier token.
        p[0] = p[1]

    # * method: p_ident_dot (rule)
    def p_ident_dot(self, p):
        '''ident_dot : ident DOT IDENTIFIER
                     | ident_dot DOT IDENTIFIER'''

        # Build a dotted identifier expression (supports chained dots like self.a.b).
        p[0] = p[1] + '.' + p[3]

    # * method: p_operator (rule)
    def p_operator(self, p):
        '''operator : PLUS
                    | MINUS
                    | LT
                    | GT
                    | LTEQ
                    | GTEQ
                    | NOTEQ
                    | STAR
                    | SLASH
                    | PERCENT
                    | DOUBLESTAR
                    | PIPE
                    | AMPERSAND
                    | EQEQ'''

        # Pass through an operator token.
        p[0] = p[1]