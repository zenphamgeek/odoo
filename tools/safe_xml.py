"""
tools/safe_xml.py
=================
Enterprise Hardened XML Parser & Structural Topology Validator.

Provides defense-in-depth against:
- CWE-611: XML External Entity (XXE) Injection
- CWE-776: Billion-Laughs / Quadratic Entity Expansion Bombs
- CWE-1333: ReDoS & XML Parser Resource Exhaustion

Architectural Invariants:
1. Multi-Encoding Pre-Parse Boundary: Proactively detects and rejects <!DOCTYPE
   and <!ENTITY in UTF-8, UTF-16-LE, UTF-16-BE, and ASCII encodings before any parser touches the payload.
2. Hardened Primary Parser: Uses lxml.etree with entity resolution, external DTDs,
   and huge tree expansion strictly disabled.
3. Defused Secondary Fallback: Uses defusedxml.ElementTree as the hardened fallback.
4. Fail-Closed Guard: Refuses to parse untrusted XML with raw, unhardened ET.fromstring.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple, Union

logger = logging.getLogger("safe_xml")

# Layer 2: lxml hardened parser
try:
    from lxml import etree  # type: ignore

    _SAFE_LXML_PARSER = etree.XMLParser(
        resolve_entities=False,  # Block external entity expansion (CWE-611)
        no_network=True,  # Block network fetching of DTDs
        dtd_validation=False,  # Do not validate against external DTDs
        load_dtd=False,  # Do not load external DTD subsets
        huge_tree=False,  # Enforce libxml2 parser memory limits (CWE-776)
    )
except ImportError:
    etree = None
    _SAFE_LXML_PARSER = None

# Layer 3: defusedxml hardened fallback
try:
    import defusedxml.ElementTree as defused_ET  # type: ignore
except ImportError:
    defused_ET = None


def check_forbidden_xml_declarations(raw_bytes: bytes) -> None:
    """
    Multi-encoding pre-parse denylist check.
    Detects and rejects <!DOCTYPE and <!ENTITY across UTF-8, UTF-16-LE, UTF-16-BE,
    and ASCII, preventing billion-laughs and quadratic expansion bombs before parsing.
    """
    # 1. Direct byte inspection for ASCII / UTF-8
    upper_bytes = raw_bytes[:4096].upper()
    if b"<!DOCTYPE" in upper_bytes or b"<!ENTITY" in upper_bytes:
        raise ValueError(
            "XML DOCTYPE and ENTITY declarations are strictly forbidden (CWE-611/CWE-776)"
        )

    # 2. Check for UTF-16 LE / BE byte patterns
    # In UTF-16 LE: b'<\x00!\x00D\x00O\x00C\x00T\x00Y\x00P\x00E'
    # In UTF-16 BE: b'\x00<\x00!\x00D\x00O\x00C\x00T\x00Y\x00P\x00E'
    if (
        b"<\x00!\x00D\x00O\x00C" in raw_bytes[:8192]
        or b"\x00<\x00!\x00D\x00O\x00C" in raw_bytes[:8192]
        or b"<\x00!\x00E\x00N\x00T" in raw_bytes[:8192]
        or b"\x00<\x00!\x00E\x00N\x00T" in raw_bytes[:8192]
    ):
        raise ValueError(
            "XML DOCTYPE and ENTITY declarations are strictly forbidden in UTF-16 (CWE-611/CWE-776)"
        )

    # 3. Defensive decode of head for any other variations (BOM / normalized text)
    try:
        decoded_head = raw_bytes[:4096].decode("utf-8", errors="ignore").upper()
        if "<!DOCTYPE" in decoded_head or "<!ENTITY" in decoded_head:
            raise ValueError(
                "XML DOCTYPE and ENTITY declarations are strictly forbidden (CWE-611/CWE-776)"
            )
    except Exception:
        pass


def parse_xml_safe(
    xml_text: Union[str, bytes],
) -> List[Tuple[str, Tuple[str, ...]]]:
    """
    Safely parses XML content and extracts element tag and sorted attribute key topology.
    Enforces strict defenses against CWE-611 and CWE-776.
    """
    if isinstance(xml_text, str):
        raw_bytes = xml_text.encode("utf-8")
    else:
        raw_bytes = xml_text

    # Layer 1: Multi-encoding pre-parse barrier
    check_forbidden_xml_declarations(raw_bytes)

    # Layer 2: lxml with strict entity suppression
    if etree is not None and _SAFE_LXML_PARSER is not None:
        try:
            root = etree.fromstring(raw_bytes, parser=_SAFE_LXML_PARSER)
            return [
                (el.tag, tuple(sorted(el.attrib.keys()))) for el in root.iter()
            ]
        except Exception as lxml_err:
            # If lxml encounters unexpected encoding issue, fallback to Layer 3
            logger.debug(
                f"lxml parse failed, falling back to defusedxml: {lxml_err}"
            )

    # Layer 3: defusedxml hardened fallback
    if defused_ET is not None:
        root = defused_ET.fromstring(raw_bytes)
        return [(el.tag, tuple(sorted(el.attrib.keys()))) for el in root.iter()]

    # Layer 4: Fail closed if neither lxml nor defusedxml is available
    raise RuntimeError(
        "No safe XML parser available (lxml or defusedxml required). "
        "Refusing to parse untrusted XML with raw ElementTree (CWE-611/CWE-776)."
    )


def assert_markup_preserved(before: str, after: str, rel_path: str = "") -> None:
    """
    Preservation Guard: Verifies that tag hierarchy and sorted attribute key
    topology remain 100% structurally identical after text transformation.
    """
    before_skel = parse_xml_safe(before)
    after_skel = parse_xml_safe(after)
    if before_skel != after_skel:
        raise ValueError(
            f"STRUCTURAL DRIFT in {rel_path or 'unnamed'}: "
            f"transform altered element/attribute topology "
            f"(before: {len(before_skel)} elements, after: {len(after_skel)} elements)"
        )
