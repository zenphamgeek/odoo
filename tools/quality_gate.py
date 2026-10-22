#!/usr/bin/env python3
"""
Forwarder for tools/quality_gate.py to enterprise/innokafe_website/tools/quality_gate.py
"""
import sys
import runpy
from pathlib import Path

target = Path(__file__).resolve().parent.parent / "enterprise" / "innokafe_website" / "tools" / "quality_gate.py"
runpy.run_path(str(target), run_name="__main__")
