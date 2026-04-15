# Utilities – ArtifactBlockParser

**Project:** Tiferet Command Parser — Educational Compiler Front-End
**Version:** 0.3.2

## Overview

`ArtifactBlockParser` is a static utility for extracting Tiferet artifact blocks from source file lines. It uses regex-based line scanning to identify the three-tier artifact comment hierarchy (`# ***`, `# **`, `# *`) and extract structured blocks for downstream processing.

**File:** `src/utils/artifact.py`


## Static Methods

### `parse_extract_filter(extract) -> Optional[Set[str]]`

Parses a comma-separated extract filter string into a set of names. Returns `None` if the input is falsy.

```python
ArtifactBlockParser.parse_extract_filter('add_error, get_error')
# {'add_error', 'get_error'}
```

### `extract_imports_block(lines) -> Optional[Dict]`

Locates and extracts the `# *** imports` section from source lines. The block spans from `# *** imports` to the next top-level `# ***` section.

Returns a block dict:
```python
{
    'name': '__imports__',
    'line_start': 0,
    'line_end': 12,
    'text': '# *** imports\n...',
    'length_chars': 245,
}
```

### `extract_group_header(lines) -> Optional[Dict]`

Locates and extracts the first non-imports top-level group header (e.g. `# *** events`).

### `extract_artifact_blocks(lines, group_type='event') -> List[Dict]`

Walks source lines and extracts all artifact blocks matching the given group type. For example, with `group_type='event'`, it finds all `# ** event: <name>` sections.

Each block in the returned list has the same dict structure as `extract_imports_block`.

```python
lines = open('sample.py').readlines()
blocks = ArtifactBlockParser.extract_artifact_blocks(lines, 'event')
# [{'name': 'add_error', 'line_start': 15, ...}, {'name': 'get_error', ...}]
```

### `filter_blocks(blocks, extract_ids) -> List[Dict]`

Applies an extract filter to a list of blocks. If `extract_ids` is `None`, returns all blocks. Otherwise, keeps only blocks whose `name` is in the set.

```python
filtered = ArtifactBlockParser.filter_blocks(blocks, {'add_error'})
# Only the add_error block
```


## Usage

```python
from src.utils import ArtifactBlockParser

# Read source file
with open('sample.py', 'r') as f:
    lines = f.readlines()

# Extract imports block
imports = ArtifactBlockParser.extract_imports_block(lines)

# Extract all event blocks
events = ArtifactBlockParser.extract_artifact_blocks(lines, 'event')

# Optionally filter to specific events
selected = ArtifactBlockParser.filter_blocks(events, {'add_error', 'get_error'})
```


## Testing

Artifact utility tests: `src/utils/tests/test_artifact.py` (13 tests)

```bash
python -m pytest src/utils/tests/test_artifact.py -v
```


## Related reading

- [lexer.md](lexer.md) — TiferetLexer (tokenizes the extracted blocks)
- [AGENTS.md](../../../AGENTS.md) — AI agent codebase index
