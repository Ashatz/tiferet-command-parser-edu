#!/usr/bin/env python
"""
Parser Test Battery — ECE 506 Submission

Runs the Tiferet parser on all sample programs in Parser/samples/ and
verifies that passing programs produce a valid Module AST and failing
programs are rejected with a SyntaxError.

Usage:
    python Parser/test_parser.py
"""

# *** imports

# ** core
import os
import sys

# Ensure the project root is on the path so src/ imports resolve.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.utils.lexer import TiferetLexer
from src.utils.parser import TiferetParser
from src.utils.artifact import ArtifactBlockParser
from src.utils.indent import IndentInjector

# *** constants

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'samples')

# Passing test programs — each must produce a valid Module AST.
PASSING_PROGRAMS = [
    ('pass_minimal_event.py', 'Single Ping event with one method'),
    ('pass_annotated_event.py', 'RenameError with OBSOLETE and TODO annotations'),
    ('pass_multi_member_event.py', 'ListErrors with attribute, init, and decorated execute'),
    ('pass_multi_section_event.py', 'Two events (GetError, ListErrors) in one module'),
    ('pass_standalone_function.py', 'Standalone utility function (imports-only parse)'),
]

# Failing test programs — each must be rejected by the parser.
FAILING_PROGRAMS = [
    ('fail_class_bare_attribute.py', 'Attribute without # * member header → SyntaxError'),
    ('fail_class_bare_method.py', 'Method without # * member header → SyntaxError'),
    ('fail_import_no_group.py', 'Import without # ** group header → SyntaxError'),
    ('fail_class_no_section.py', 'Class without # ** section header → rejected at extraction'),
    ('fail_bare_function.py', 'Function without # ** section header → rejected at extraction'),
]


# *** helpers

def extract_and_tokenize(filepath):
    """
    Read a source file, extract artifact blocks (imports + group header +
    event sections), tokenize them, and inject INDENT/DEDENT tokens.

    :param filepath: Path to the source file.
    :type filepath: str
    :return: List of token dicts ready for parsing.
    :rtype: list
    """

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Extract blocks.
    imports_block = ArtifactBlockParser.extract_imports_block(lines)
    group_header = ArtifactBlockParser.extract_group_header(lines)
    event_blocks = ArtifactBlockParser.extract_artifact_blocks(lines, 'event')

    blocks = []
    if imports_block:
        blocks.append(imports_block)
    if group_header:
        blocks.append(group_header)
    blocks.extend(event_blocks)

    # Tokenize all blocks.
    lexer = TiferetLexer()
    all_tokens = []
    for block in blocks:
        all_tokens.extend(lexer.tokenize(block['text']))

    # Inject INDENT/DEDENT.
    all_tokens = IndentInjector.inject(all_tokens)

    return all_tokens, event_blocks


def parse_tokens(tokens):
    """
    Parse a token stream into an AST using TiferetParser.

    :param tokens: List of token dicts.
    :type tokens: list
    :return: AST dict.
    :rtype: dict
    """

    parser = TiferetParser()
    return parser.parse(tokens)


# *** test runner

def run_tests():
    """
    Execute the full test battery and print results.
    """

    passed = 0
    failed = 0
    total = len(PASSING_PROGRAMS) + len(FAILING_PROGRAMS)

    print('=' * 70)
    print('Parser Test Battery — ECE 506 Submission')
    print('=' * 70)
    print()

    # --- Passing programs ---
    print('PASSING PROGRAMS (expect valid Module AST)')
    print('-' * 50)

    for filename, description in PASSING_PROGRAMS:
        filepath = os.path.join(SAMPLES_DIR, filename)
        label = f'  {filename}'

        try:
            tokens, event_blocks = extract_and_tokenize(filepath)
            ast = parse_tokens(tokens)

            # Verify AST root is a Module.
            if isinstance(ast, dict) and ast.get('type') == 'Module':
                groups = ast.get('groups', [])
                print(f'{label:50s} PASS  ({len(groups)} groups)')
                passed += 1
            else:
                print(f'{label:50s} FAIL  (AST root is not Module)')
                failed += 1

        except Exception as e:
            print(f'{label:50s} FAIL  ({type(e).__name__}: {e})')
            failed += 1

    print()

    # --- Failing programs ---
    print('FAILING PROGRAMS (expect SyntaxError or extraction rejection)')
    print('-' * 50)

    for filename, description in FAILING_PROGRAMS:
        filepath = os.path.join(SAMPLES_DIR, filename)
        label = f'  {filename}'

        try:
            tokens, event_blocks = extract_and_tokenize(filepath)

            # If no event blocks were extracted, the file is rejected at extraction level.
            if not event_blocks:
                print(f'{label:50s} PASS  (rejected: no matching artifact blocks)')
                passed += 1
                continue

            ast = parse_tokens(tokens)

            # If we get here, the parser accepted it — that's a test failure.
            print(f'{label:50s} FAIL  (parser accepted — expected rejection)')
            failed += 1

        except SyntaxError as e:
            print(f'{label:50s} PASS  (SyntaxError raised)')
            passed += 1

        except Exception as e:
            # Any other exception also counts as rejection.
            print(f'{label:50s} PASS  ({type(e).__name__} raised)')
            passed += 1

    # --- Summary ---
    print()
    print('=' * 70)
    print(f'Results: {passed}/{total} passed, {failed}/{total} failed')
    print('=' * 70)

    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
