"""Scan Output Writer Utility"""

# *** imports

# ** core
import os
import json
from typing import Dict, Any, List, Optional

# ** infra
import yaml

# *** utils

# ** util: anchored_dumper
class AnchoredDumper(yaml.Dumper):
    '''
    Custom YAML Dumper that assigns meaningful anchor names from a registry
    instead of auto-generated id001-style labels.
    '''

    # * attribute: anchor_registry
    anchor_registry: dict

    # * attribute: _node_anchors
    _node_anchors: dict

    # * init
    def __init__(self, *args, anchor_registry: dict = None, **kwargs):
        '''
        Initialize with an optional anchor registry.

        :param anchor_registry: Dict mapping id(python_obj) to anchor name string.
        :type anchor_registry: dict
        '''

        super().__init__(*args, **kwargs)

        # Store the registry for anchor name lookups.
        self.anchor_registry = anchor_registry or {}

        # Internal mapping from id(yaml.Node) to anchor name, built during representation.
        self._node_anchors = {}

    # * method: represent_sequence
    def represent_sequence(self, tag, sequence, flow_style=None):
        '''
        Override to capture the mapping from YAML node to anchor name
        when the source Python sequence is in the anchor registry.

        :param tag: The YAML tag.
        :type tag: str
        :param sequence: The Python sequence being represented.
        :type sequence: list
        :param flow_style: Optional flow style override.
        :type flow_style: bool
        :return: The YAML sequence node.
        :rtype: yaml.SequenceNode
        '''

        # Create the node via the parent representer.
        node = super().represent_sequence(tag, sequence, flow_style)

        # If this Python list is registered, map its node for generate_anchor.
        if id(sequence) in self.anchor_registry:
            self._node_anchors[id(node)] = self.anchor_registry[id(sequence)]

        return node

    # * method: generate_anchor
    def generate_anchor(self, node):
        '''
        Return a meaningful anchor name if this node was registered during
        representation, otherwise fall back to the default.

        :param node: The YAML representation node.
        :type node: yaml.Node
        :return: The anchor name string.
        :rtype: str
        '''

        # Check if this node was registered during represent_sequence.
        anchor = self._node_anchors.get(id(node), None)
        if anchor:
            return anchor

        # Fall back to default behavior.
        return super().generate_anchor(node)


# ** util: scan_output_writer
class ScanOutputWriter:
    '''
    Utility for writing scan result payloads to file.
    Supports YAML and JSON formats with auto-detection from file extension.
    '''

    # * method: detect_format (static)
    @staticmethod
    def detect_format(output_path: str, output_format: str = 'auto') -> str:
        '''
        Resolve the output format. If ``output_format`` is ``'auto'``,
        detect from the file extension; otherwise return ``output_format``
        unchanged.

        :param output_path: The target file path.
        :type output_path: str
        :param output_format: Explicit format or ``'auto'`` for detection.
        :type output_format: str
        :return: Resolved format string (``'yaml'``, ``'json'``, or ``'keter'``).
        :rtype: str
        '''

        # Auto-detect format from file extension.
        if output_format == 'auto':
            ext = os.path.splitext(output_path)[1].lower()
            if ext == '.json':
                return 'json'
            if ext == '.keter':
                return 'keter'
            return 'yaml'

        # Return the explicit format.
        return output_format

    # * method: write (static)
    @staticmethod
    def write(result: Dict[str, Any],
            output_path: str,
            output_format: str = 'auto',
            anchor_registry: Dict[int, str] = None,
        ) -> None:
        '''
        Write a result payload to a file in the specified format.

        :param result: The result payload to write.
        :type result: Dict[str, Any]
        :param output_path: The file path to write to.
        :type output_path: str
        :param output_format: The output format (``'yaml'``, ``'json'``, or ``'auto'``).
        :type output_format: str
        :param anchor_registry: Optional anchor registry for YAML anchor names.
        :type anchor_registry: Dict[int, str]
        '''

        # Resolve the format.
        fmt = ScanOutputWriter.detect_format(output_path, output_format)

        # Write the output file.
        with open(output_path, 'w', encoding='utf-8') as f:
            if fmt == 'json':
                json.dump(result, f, indent=2, default=str)
            elif fmt == 'keter':
                f.write(result if isinstance(result, str) else str(result))
            elif anchor_registry:
                yaml.dump(
                    result, f,
                    Dumper=lambda *a, **kw: AnchoredDumper(
                        *a, anchor_registry=anchor_registry, **kw,
                    ),
                    default_flow_style=False,
                    sort_keys=False,
                )
            else:
                yaml.dump(result, f, default_flow_style=False, sort_keys=False)

    # * method: parse_extract_names (static)
    @staticmethod
    def parse_extract_names(extract: str) -> Optional[List[str]]:
        '''
        Parse a comma-separated extract filter string into a list of names
        suitable for inclusion in the output payload.

        :param extract: Comma-separated artifact names, or None.
        :type extract: str
        :return: A list of stripped names, or None if extract is falsy.
        :rtype: Optional[List[str]]
        '''

        # Return None if no filter provided.
        if not extract:
            return None

        # Split, strip, and return as a list.
        return [name.strip() for name in extract.split(',')]
