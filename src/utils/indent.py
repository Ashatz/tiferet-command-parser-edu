"""Indent Injector Utility"""

# *** imports

# ** core
import re
from typing import List, Dict, Any

# *** utils

# ** util: indent_injector
class IndentInjector:
    '''
    Post-tokenization utility that injects INDENT and DEDENT tokens
    into a PLY token stream within method and init artifact member bodies.

    Enters method-body mode after an ARTIFACT_MEMBER token whose value
    matches ``# * method:`` or ``# * init``. Tracks indentation depth
    via a column stack, guarded by parenthesis depth so multi-line
    function signatures are ignored. Exits on the next artifact comment
    at the same or higher structural level.
    '''

    # * method: inject (static)
    @staticmethod
    def inject(tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        '''
        Inject INDENT and DEDENT tokens into a flat PLY token stream.

        :param tokens: Flat token list produced by the PLY lexer.
        :type tokens: List[Dict[str, Any]]
        :return: Token list with INDENT and DEDENT tokens injected
                 at class-body and method-body indentation boundaries.
        :rtype: List[Dict[str, Any]]
        '''

        # Compile the pattern that identifies method and init members.
        method_pattern = re.compile(r'#\s*\*\s+(method:|init\b)')

        # Token types that signal the end of an open method body.
        exits_body = {
            'ARTIFACT_MEMBER',
            'ARTIFACT_SECTION',
            'ARTIFACT_START',
            'ARTIFACT_IMPORTS_START',
            'ARTIFACT_IMPORT_GROUP',
        }

        # Annotation tokens that close a method body only when body content exists.
        annotation_exits = {'OBSOLETE', 'TODO'}

        result = []
        in_method_body = False
        member_col = None
        indent_stack = []
        paren_depth = 0

        # Class body tracking.
        in_class_body = False
        class_col = None
        saw_class = False

        i = 0
        while i < len(tokens):
            tok = tokens[i]

            # Track open/close depth to ignore indentation inside signatures.
            if tok['type'] in ('LPAREN', 'LBRACK', 'LBRACE'):
                paren_depth += 1
            elif tok['type'] in ('RPAREN', 'RBRACK', 'RBRACE'):
                paren_depth = max(0, paren_depth - 1)

            # Detect CLASS token to prepare for class body injection.
            if tok['type'] == 'CLASS':
                saw_class = True
                class_col = tok['column']

            # Artifact member token — close any open body, optionally open new one.
            if tok['type'] == 'ARTIFACT_MEMBER':

                # Flush remaining DEDENTs for the closing body.
                while indent_stack:
                    result.append({
                        'type': 'DEDENT', 'value': '',
                        'line': tok['line'], 'column': tok['column'],
                    })
                    indent_stack.pop()

                # Reset body state.
                in_method_body = False
                member_col = None
                paren_depth = 0

                # Enter body mode if this member is a method or init.
                if method_pattern.search(tok['value']):
                    in_method_body = True
                    member_col = tok['column']

            # Section or start token — close any open class and method bodies.
            elif tok['type'] in ('ARTIFACT_SECTION', 'ARTIFACT_START', 'ARTIFACT_IMPORTS_START'):
                while indent_stack:
                    result.append({
                        'type': 'DEDENT', 'value': '',
                        'line': tok['line'], 'column': tok['column'],
                    })
                    indent_stack.pop()
                if in_class_body:
                    result.append({
                        'type': 'DEDENT', 'value': '',
                        'line': tok['line'], 'column': tok['column'],
                    })
                    in_class_body = False
                    class_col = None
                in_method_body = False
                member_col = None
                paren_depth = 0

            # After CLASS ... COLON NEWLINE, inject INDENT for class body.
            if saw_class and tok['type'] == 'NEWLINE' and paren_depth == 0:
                result.append(tok)
                i += 1

                # Consume any consecutive newlines.
                while i < len(tokens) and tokens[i]['type'] == 'NEWLINE':
                    result.append(tokens[i])
                    i += 1

                # Check if we just passed a COLON before this NEWLINE.
                colon_before = False
                for j in range(len(result) - 1, -1, -1):
                    if result[j]['type'] == 'NEWLINE':
                        continue
                    colon_before = result[j]['type'] == 'COLON'
                    break

                if colon_before and i < len(tokens):
                    next_tok = tokens[i]
                    if next_tok['column'] > class_col:
                        result.append({
                            'type': 'INDENT', 'value': '',
                            'line': next_tok['line'], 'column': next_tok['column'],
                        })
                        in_class_body = True
                        saw_class = False
                        continue

                saw_class = False
                continue

            # Inject INDENT/DEDENT after each newline inside a method body.
            if in_method_body and tok['type'] == 'NEWLINE' and paren_depth == 0:
                result.append(tok)
                i += 1

                # Consume any consecutive newlines.
                while i < len(tokens) and tokens[i]['type'] == 'NEWLINE':
                    result.append(tokens[i])
                    i += 1

                if i < len(tokens):
                    next_tok = tokens[i]
                    next_col = next_tok['column']

                    # Next artifact comment closes the body.
                    if next_tok['type'] in exits_body or (
                        next_tok['type'] in annotation_exits and indent_stack
                    ):
                        while indent_stack:
                            result.append({
                                'type': 'DEDENT', 'value': '',
                                'line': next_tok['line'], 'column': next_tok['column'],
                            })
                            indent_stack.pop()
                        in_method_body = False
                        member_col = None

                    # Only track lines that are deeper than the member column.
                    elif next_col > member_col:
                        current = indent_stack[-1] if indent_stack else None

                        if current is None:

                            # First body line — establish the indent baseline.
                            indent_stack.append(next_col)
                            result.append({
                                'type': 'INDENT', 'value': '',
                                'line': next_tok['line'], 'column': next_col,
                            })

                        elif next_col > current:

                            # Deeper nesting level.
                            indent_stack.append(next_col)
                            result.append({
                                'type': 'INDENT', 'value': '',
                                'line': next_tok['line'], 'column': next_col,
                            })

                        elif next_col < current:

                            # Dedent one or more levels.
                            while indent_stack and indent_stack[-1] > next_col:
                                indent_stack.pop()
                                result.append({
                                    'type': 'DEDENT', 'value': '',
                                    'line': next_tok['line'], 'column': next_col,
                                })

                continue

            result.append(tok)
            i += 1

        # Close any method body still open at end of stream.
        last_line = tokens[-1]['line'] if tokens else 0
        while indent_stack:
            result.append({
                'type': 'DEDENT', 'value': '',
                'line': last_line, 'column': 0,
            })
            indent_stack.pop()

        # Close any class body still open at end of stream.
        if in_class_body:
            result.append({
                'type': 'DEDENT', 'value': '',
                'line': last_line, 'column': 0,
            })

        # Return the enriched token stream.
        return result
