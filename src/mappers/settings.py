"""Tiferet Compiler Mapper Base Classes"""

# *** imports

# ** core
from typing import List, Tuple

# *** constants
# The KT_* constants below mirror the token-type tags emitted by
# KeterLexer in src/utils/lexer_keter.py. They are kept here as
# module-level constants so KeterTransferObject does not need to
# import KeterLexer (which would create a circular dependency on
# the utils package).

# ** constant: kt_keyword
KT_KEYWORD = 'KEYWORD'

# ** constant: kt_string
KT_STRING = 'STRING'

# ** constant: kt_ident
KT_IDENT = 'IDENT'

# ** constant: kt_lparen
KT_LPAREN = 'LPAREN'

# ** constant: kt_rparen
KT_RPAREN = 'RPAREN'

# ** constant: kt_comma
KT_COMMA = 'COMMA'

# *** classes

# ** class: keter_transfer_base
class KeterTransferObject:
    '''
    Base class providing shared token-stream traversal helpers
    for all Keter* transfer objects.
    '''

    # * method: consume (static)
    @staticmethod
    def consume(tokens: List[Tuple[str, str]],
            pos: List[int],
            expected_type: str = None,
            expected_value: str = None,
        ) -> Tuple[str, str]:
        '''
        Consume and return the current token, optionally asserting type/value.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :param expected_type: Expected token type.
        :type expected_type: str
        :param expected_value: Expected token value.
        :type expected_value: str
        :return: The consumed (type, value) tuple.
        :rtype: Tuple[str, str]
        '''

        # Validate bounds.
        if pos[0] >= len(tokens):
            raise ValueError(
                f'Unexpected end of keter input'
                f' (expected {expected_type}:{expected_value})'
            )

        # Get the current token.
        tok = tokens[pos[0]]

        # Assert type if specified.
        if expected_type and tok[0] != expected_type:
            raise ValueError(
                f'Expected {expected_type} but got'
                f' {tok[0]}:"{tok[1]}" at position {pos[0]}'
            )

        # Assert value if specified.
        if expected_value and tok[1] != expected_value:
            raise ValueError(
                f'Expected "{expected_value}" but got'
                f' "{tok[1]}" at position {pos[0]}'
            )

        # Advance and return.
        pos[0] += 1
        return tok

    # * method: peek (static)
    @staticmethod
    def peek(tokens: List[Tuple[str, str]],
            pos: List[int],
        ) -> Tuple[str, str] | None:
        '''
        Peek at the current token without consuming it.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The current token, or None if exhausted.
        :rtype: Tuple[str, str] | None
        '''

        # Return the current token if within bounds.
        if pos[0] < len(tokens):
            return tokens[pos[0]]
        return None

    # * method: skip_comma (static)
    @staticmethod
    def skip_comma(tokens: List[Tuple[str, str]],
            pos: List[int],
        ) -> None:
        '''
        Consume a comma token if the current token is one.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        '''

        # Skip an optional trailing comma.
        cur = KeterTransferObject.peek(tokens, pos)
        if cur and cur[0] == KT_COMMA:
            pos[0] += 1

    # * method: collect_balanced (static)
    @staticmethod
    def collect_balanced(tokens: List[Tuple[str, str]],
            pos: List[int],
        ) -> str:
        '''
        Collect tokens until the matching closing paren at depth 0,
        reconstructing the raw expression string.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The raw expression string.
        :rtype: str
        '''

        # Track parenthesis depth and accumulate parts.
        depth = 0
        parts: List[str] = []

        while pos[0] < len(tokens):
            tok = tokens[pos[0]]

            # Stop at the matching closing paren.
            if tok[0] == KT_RPAREN and depth == 0:
                break

            # Track nested parens.
            if tok[0] == KT_LPAREN:
                depth += 1
                parts.append('(')
            elif tok[0] == KT_RPAREN:
                depth -= 1
                parts.append(')')
            elif tok[0] == KT_COMMA:
                parts.append(', ')
            elif tok[0] == KT_STRING:
                parts.append(f'"{tok[1]}"')
            else:
                parts.append(tok[1])

            pos[0] += 1

        # Return the reconstructed expression.
        return ''.join(parts)

    # * method: decode_param_spec (static)
    @staticmethod
    def decode_param_spec(spec: str) -> dict:
        '''
        Decode a colon-delimited param spec into a dict of IRParam fields.

        :param spec: The colon-delimited string (name:type:required:default:description).
        :type spec: str
        :return: Dict with name, type, required, default, description keys.
        :rtype: dict
        '''

        # Split and assign positionally.
        parts = spec.split(':')
        return dict(
            name=parts[0] if len(parts) > 0 else '',
            type=parts[1] if len(parts) > 1 else '',
            required=parts[2].lower() == 'true' if len(parts) > 2 else True,
            default=parts[3] if len(parts) > 3 else '',
            description=':'.join(parts[4:]) if len(parts) > 4 else '',
        )

    # * method: decode_return_spec (static)
    @staticmethod
    def decode_return_spec(spec: str) -> dict:
        '''
        Decode a colon-delimited return spec into a dict of IRReturn fields.

        :param spec: The colon-delimited string (type_name:description).
        :type spec: str
        :return: Dict with type_name and description keys.
        :rtype: dict
        '''

        # Split on first colon only.
        parts = spec.split(':', 1)
        return dict(
            type_name=parts[0] if len(parts) > 0 else '',
            description=parts[1] if len(parts) > 1 else '',
        )
