from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

@dataclass
class PDMDirective:
    """Base class for all PDM directives."""
    op: str
    original_data: Dict[str, Any]

@dataclass
class ScaffoldNounDirective(PDMDirective):
    target: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'ScaffoldNounDirective':
        target = d.get('target') or d.get('name') or d.get('noun')
        if not target:
            raise ValueError("Missing required field for scaffold_noun: 'target', 'name', or 'noun'")
        return cls(op='scaffold_noun', original_data=d, target=target)

@dataclass
class ScaffoldVerbDirective(PDMDirective):
    noun: str
    verb: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'ScaffoldVerbDirective':
        noun = d.get('noun') or d.get('target')
        verb = d.get('verb') or d.get('name')
        if not noun:
            raise ValueError("Missing required field for scaffold_verb: 'noun' or 'target'")
        if not verb:
            raise ValueError("Missing required field for scaffold_verb: 'verb' or 'name'")
        return cls(op='scaffold_verb', original_data=d, noun=noun, verb=verb)

@dataclass
class InjectCodeDirective(PDMDirective):
    file_path: str
    anchor_text: str
    position: str
    directive_text: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'InjectCodeDirective':
        file_path = d.get('file') or d.get('path')
        if not file_path:
            raise ValueError("Missing required field for inject_code: 'file' or 'path'")
        
        anchor_text = d.get('anchor_text', '')
        position = d.get('position', 'replace')
        directive_text = d.get('directive') or d.get('content') or ""
        
        return cls(
            op='inject_code', 
            original_data=d, 
            file_path=file_path, 
            anchor_text=anchor_text, 
            position=position, 
            directive_text=directive_text
        )

@dataclass
class VerifyDirective(PDMDirective):
    against: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'VerifyDirective':
        return cls(op='verify', original_data=d, against=d.get('against', ''))

@dataclass
class SnapshotDirective(PDMDirective):
    label: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'SnapshotDirective':
        return cls(op='snapshot', original_data=d, label=d.get('label', 'baseline_snapshot'))

def parse_directive(d: Dict[str, Any]) -> PDMDirective:
    """Factory to convert a raw dictionary into a strictly typed PDMDirective."""
    op = d.get('op')
    if not op:
        raise ValueError(f"Missing 'op' key in directive: {d}")
        
    if op == 'scaffold_noun':
        return ScaffoldNounDirective.from_dict(d)
    elif op == 'scaffold_verb':
        return ScaffoldVerbDirective.from_dict(d)
    elif op == 'inject_code':
        return InjectCodeDirective.from_dict(d)
    elif op == 'verify':
        return VerifyDirective.from_dict(d)
    elif op == 'snapshot':
        return SnapshotDirective.from_dict(d)
    else:
        # Fallback for unknown operations, returning the base class
        return PDMDirective(op=op, original_data=d)
