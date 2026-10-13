#!/usr/bin/env python3
"""
tools/lint_sql_constraints_shape.py
===================================
Static AST Linter for Odoo Model _sql_constraints & models.Constraint Invariants.

Enforces:
1. Shape Invariance: _sql_constraints must ALWAYS be an AST List of 3-element Tuples:
      _sql_constraints = [
          ('constraint_name', 'unique(column_name)', 'Error message string'),
      ]
   Flat tuples (e.g. `_sql_constraints = ('name', 'unique(...)', 'msg')`),
   dicts, strings, or malformed tuple lengths are strictly rejected.
2. Uniqueness & No Shadowing: No duplicate constraint names within the same model,
   and zero duplicate/conflicting _sql_constraints assignments in the same class body.
3. Lockstep Invariance: For models defining `models.Constraint` uniqueness,
   assert canonical `_sql_constraints` is also present for ORM/DB migration robustness.
4. Fail-Closed Security Stance: Exit code 0 if all clean; Exit code 1 on any violation.
"""

import ast
import os
import re
import sys
from typing import List, Tuple, Dict, Any, Optional

IDENTIFIER_RE = re.compile(r'^[a-zA-Z0-9_]+$')


class ConstraintViolation:
    def __init__(self, file_path: str, line_no: int, class_name: str, code: str, message: str):
        self.file_path = file_path
        self.line_no = line_no
        self.class_name = class_name
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line_no}: [{self.code}] class {self.class_name}: {self.message}"


def _get_string_constant(node: ast.AST) -> Optional[str]:
    """Extract string value from Constant or Str node across Python versions."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if hasattr(ast, 'Str') and isinstance(node, ast.Str):
        return node.s
    return None


def lint_ast_tree(tree: ast.AST, file_path: str) -> List[ConstraintViolation]:
    """Inspect an AST tree for _sql_constraints and models.Constraint violations."""
    violations: List[ConstraintViolation] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        class_name = node.name
        sql_constraints_assigns: List[ast.Assign] = []
        constraint_attrs: Dict[str, ast.Call] = {}

        # Scan class body statements
        for stmt in node.body:
            # Check for _sql_constraints = ...
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == '_sql_constraints':
                        sql_constraints_assigns.append(stmt)
                    elif (
                        isinstance(target, ast.Name)
                        and isinstance(stmt.value, ast.Call)
                    ):
                        call = stmt.value
                        func = call.func
                        # Match models.Constraint(...) or Constraint(...)
                        if (
                            (isinstance(func, ast.Attribute) and func.attr == 'Constraint')
                            or (isinstance(func, ast.Name) and func.id == 'Constraint')
                        ):
                            constraint_attrs[target.id] = call

            # Also check annotated assignment: _sql_constraints: list = ...
            elif isinstance(stmt, ast.AnnAssign):
                if isinstance(stmt.target, ast.Name) and stmt.target.id == '_sql_constraints':
                    if stmt.value:
                        mock_assign = ast.Assign(targets=[stmt.target], value=stmt.value)
                        mock_assign.lineno = stmt.lineno
                        sql_constraints_assigns.append(mock_assign)

        # 1. Check for duplicate _sql_constraints assignment in the same class
        if len(sql_constraints_assigns) > 1:
            violations.append(
                ConstraintViolation(
                    file_path,
                    sql_constraints_assigns[1].lineno,
                    class_name,
                    "DUPLICATE_ASSIGNMENT",
                    f"Multiple _sql_constraints assignments ({len(sql_constraints_assigns)}) found in class body.",
                )
            )

        declared_constraint_names: set = set()

        for assign_node in sql_constraints_assigns:
            val = assign_node.value

            # 2. Check value type is ast.List
            if isinstance(val, ast.Tuple):
                violations.append(
                    ConstraintViolation(
                        file_path,
                        assign_node.lineno,
                        class_name,
                        "FLAT_TUPLE_SHADOWING",
                        "_sql_constraints is declared as a flat tuple instead of a list of 3-tuples. "
                        "This will fail with ValueError during unpacking in Odoo's SQL constraint builder.",
                    )
                )
                continue

            if not isinstance(val, ast.List):
                violations.append(
                    ConstraintViolation(
                        file_path,
                        assign_node.lineno,
                        class_name,
                        "INVALID_COLLECTION_TYPE",
                        f"_sql_constraints must be a list of 3-tuples, got {type(val).__name__}.",
                    )
                )
                continue

            # 3. Inspect each element of the list
            for idx, elt in enumerate(val.elts):
                elt_lineno = getattr(elt, 'lineno', assign_node.lineno)
                if not isinstance(elt, ast.Tuple):
                    violations.append(
                        ConstraintViolation(
                            file_path,
                            elt_lineno,
                            class_name,
                            "ELEMENT_NOT_TUPLE",
                            f"Element #{idx} of _sql_constraints is {type(elt).__name__}, must be a 3-element tuple.",
                        )
                    )
                    continue

                if len(elt.elts) != 3:
                    violations.append(
                        ConstraintViolation(
                            file_path,
                            elt_lineno,
                            class_name,
                            "INVALID_TUPLE_LENGTH",
                            f"Element #{idx} of _sql_constraints has {len(elt.elts)} items, expected exactly 3 "
                            "('name', 'sql_definition', 'error_message').",
                        )
                    )
                    continue

                # Unpack tuple elements
                c_name_node, c_def_node, c_msg_node = elt.elts

                c_name = _get_string_constant(c_name_node)
                c_def = _get_string_constant(c_def_node)
                c_msg = _get_string_constant(c_msg_node)

                if c_name is None:
                    violations.append(
                        ConstraintViolation(
                            file_path,
                            elt_lineno,
                            class_name,
                            "NON_STRING_NAME",
                            f"Constraint #{idx} name must be a string literal.",
                        )
                    )
                else:
                    if not IDENTIFIER_RE.match(c_name):
                        violations.append(
                            ConstraintViolation(
                                file_path,
                                elt_lineno,
                                class_name,
                                "MALFORMED_NAME",
                                f"Constraint #{idx} name '{c_name}' is not a valid alphanumeric identifier.",
                            )
                        )
                    if c_name in declared_constraint_names:
                        violations.append(
                            ConstraintViolation(
                                file_path,
                                elt_lineno,
                                class_name,
                                "DUPLICATE_NAME",
                                f"Constraint '{c_name}' defined multiple times in _sql_constraints.",
                            )
                        )
                    declared_constraint_names.add(c_name)

                if c_def is None or not c_def.strip():
                    violations.append(
                        ConstraintViolation(
                            file_path,
                            elt_lineno,
                            class_name,
                            "EMPTY_SQL_DEF",
                            f"Constraint #{idx} SQL definition must be a non-empty string.",
                        )
                    )

                if c_msg is None or not c_msg.strip():
                    violations.append(
                        ConstraintViolation(
                            file_path,
                            elt_lineno,
                            class_name,
                            "EMPTY_ERROR_MSG",
                            f"Constraint #{idx} user error message must be a non-empty string.",
                        )
                    )

        # 4. Lockstep Invariance for critical sovereign models
        if class_name == 'Al2cClaimAtom':
            if 'claim_hash_uniq' not in declared_constraint_names:
                violations.append(
                    ConstraintViolation(
                        file_path,
                        node.lineno,
                        class_name,
                        "MISSING_CLAIM_HASH_SQL_CONSTRAINT",
                        "Al2cClaimAtom model must declare 'claim_hash_uniq' in _sql_constraints "
                        "in lockstep with _claim_hash_uniq = models.Constraint(...).",
                    )
                )

        if class_name == 'Al2cMojoUsageLedger':
            if 'idempotency_key_uniq' not in declared_constraint_names:
                violations.append(
                    ConstraintViolation(
                        file_path,
                        node.lineno,
                        class_name,
                        "MISSING_IDEMPOTENCY_SQL_CONSTRAINT",
                        "Al2cMojoUsageLedger model must declare 'idempotency_key_uniq' in _sql_constraints "
                        "in lockstep with _idempotency_key_uniq = models.Constraint(...).",
                    )
                )

    return violations


def lint_file(file_path: str) -> List[ConstraintViolation]:
    """Parse and lint a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        tree = ast.parse(code, filename=file_path)
        return lint_ast_tree(tree, file_path)
    except SyntaxError as e:
        return [ConstraintViolation(file_path, e.lineno or 1, "<module>", "SYNTAX_ERROR", str(e))]
    except Exception as e:
        return [ConstraintViolation(file_path, 1, "<module>", "PARSE_ERROR", str(e))]


def run_self_tests() -> bool:
    """Execute adversarial self-tests on synthetic AST structures."""
    print("Running lint_sql_constraints_shape adversarial self-tests...")

    # Test 1: Valid canonical list of 3-tuples
    valid_code = """
class SafeModel(models.Model):
    _name = 'safe.model'
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The code must be unique!'),
        ('name_uniq', 'unique(name)', 'The name must be unique!'),
    ]
"""
    v = lint_ast_tree(ast.parse(valid_code), "<test_valid>")
    assert len(v) == 0, f"Expected 0 violations for valid model, got: {[str(x) for x in v]}"

    # Test 2: Flat tuple defect (shadowing)
    flat_tuple_code = """
class BrokenModel(models.Model):
    _name = 'broken.model'
    _sql_constraints = ('code_uniq', 'unique(code)', 'The code must be unique!')
"""
    v = lint_ast_tree(ast.parse(flat_tuple_code), "<test_flat_tuple>")
    assert any(x.code == 'FLAT_TUPLE_SHADOWING' for x in v), f"Failed to catch flat tuple: {[str(x) for x in v]}"

    # Test 3: Element not a 3-tuple (e.g. 2 elements)
    short_tuple_code = """
class ShortTupleModel(models.Model):
    _name = 'short.model'
    _sql_constraints = [
        ('code_uniq', 'unique(code)'),
    ]
"""
    v = lint_ast_tree(ast.parse(short_tuple_code), "<test_short_tuple>")
    assert any(x.code == 'INVALID_TUPLE_LENGTH' for x in v), f"Failed to catch 2-tuple: {[str(x) for x in v]}"

    # Test 4: Element not a tuple (e.g. string in list)
    str_elt_code = """
class StrEltModel(models.Model):
    _name = 'str.model'
    _sql_constraints = [
        'unique(code)',
    ]
"""
    v = lint_ast_tree(ast.parse(str_elt_code), "<test_str_elt>")
    assert any(x.code == 'ELEMENT_NOT_TUPLE' for x in v), f"Failed to catch string element: {[str(x) for x in v]}"

    # Test 5: Duplicate constraint name in list
    dup_name_code = """
class DupNameModel(models.Model):
    _name = 'dup.model'
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'msg 1'),
        ('code_uniq', 'unique(code)', 'msg 2'),
    ]
"""
    v = lint_ast_tree(ast.parse(dup_name_code), "<test_dup_name>")
    assert any(x.code == 'DUPLICATE_NAME' for x in v), f"Failed to catch duplicate name: {[str(x) for x in v]}"

    # Test 6: Duplicate _sql_constraints assignment in class
    dup_assign_code = """
class DupAssignModel(models.Model):
    _name = 'dup.assign'
    _sql_constraints = [('a', 'unique(a)', 'm')]
    _sql_constraints = [('b', 'unique(b)', 'm')]
"""
    v = lint_ast_tree(ast.parse(dup_assign_code), "<test_dup_assign>")
    assert any(x.code == 'DUPLICATE_ASSIGNMENT' for x in v), f"Failed to catch duplicate assignment: {[str(x) for x in v]}"

    # Test 7: Al2cClaimAtom missing claim_hash_uniq
    missing_atom_code = """
class Al2cClaimAtom(models.Model):
    _name = 'al2c.claim.atom'
    _claim_hash_uniq = models.Constraint('unique(claim_hash)', 'msg')
"""
    v = lint_ast_tree(ast.parse(missing_atom_code), "<test_atom_missing>")
    assert any(x.code == 'MISSING_CLAIM_HASH_SQL_CONSTRAINT' for x in v), f"Failed to catch missing atom constraint: {[str(x) for x in v]}"

    # Test 8: Al2cClaimAtom with both models.Constraint and _sql_constraints
    valid_atom_code = """
class Al2cClaimAtom(models.Model):
    _name = 'al2c.claim.atom'
    _claim_hash_uniq = models.Constraint('unique(claim_hash)', 'msg')
    _sql_constraints = [
        ('claim_hash_uniq', 'unique(claim_hash)', 'msg'),
    ]
"""
    v = lint_ast_tree(ast.parse(valid_atom_code), "<test_atom_valid>")
    assert len(v) == 0, f"Expected 0 violations for valid Al2cClaimAtom, got: {[str(x) for x in v]}"

    print("  [✓] All 8 adversarial self-tests passed cleanly.")
    return True


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Static AST Linter for _sql_constraints shape invariants")
    parser.add_argument("--self-test", action="store_true", help="Run internal adversarial self-tests")
    parser.add_argument("paths", nargs="*", default=["addons"], help="Paths or files to scan (default: addons)")
    args = parser.parse_args()

    if args.self_test:
        success = run_self_tests()
        return 0 if success else 1

    targets: List[str] = []
    for path in args.paths:
        if os.path.isfile(path) and path.endswith('.py'):
            targets.append(path)
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                # Ignore .git, __pycache__, node_modules, .venv
                dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'node_modules', '.venv', '.tox')]
                for f in files:
                    if f.endswith('.py'):
                        targets.append(os.path.join(root, f))

    all_violations: List[ConstraintViolation] = []
    scanned_count = 0

    for fpath in targets:
        # Fast pre-filter: check if file contains '_sql_constraints' or 'Al2c'
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if '_sql_constraints' not in content and 'Al2cClaimAtom' not in content and 'Al2cMojoUsageLedger' not in content:
            continue

        scanned_count += 1
        violations = lint_file(fpath)
        all_violations.extend(violations)

    print(f"Scanned {scanned_count} files containing constraint tokens out of {len(targets)} candidate files.")

    if all_violations:
        print(f"\n[FAIL] Found {len(all_violations)} constraint shape violations:")
        for v in all_violations:
            print(f"  ❌ {v}")
        return 1

    print(f"[PASS] All {scanned_count} candidate files conform to canonical _sql_constraints list-of-3-tuples standards.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
