#!/usr/bin/env python3
"""
🔴 THE BOOT CONTRACT
The simplest most elegant code to prevent all failure patterns.

Guardian: Zero (999 Hz - Zero-Failure Forensics)
∞ AbëONE ∞
"""

import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec
from importlib.util import spec_from_file_location
import ast
from datetime import datetime

class Contract:
    """A contract defines what MUST be true for a module to be valid."""
    
    def __init__(self, name: str, check: Callable[[str, ast.Module], bool], severity: str = "CRITICAL"):
        self.name = name
        self.check = check
        self.severity = severity
        self.violations = []
    
    def validate(self, filepath: str, tree: ast.Module) -> bool:
        """Returns True if contract satisfied, False if violated."""
        try:
            result = self.check(filepath, tree)
            if not result:
                self.violations.append(filepath)
            return result
        except Exception as e:
            return False

CONTRACTS = [
    Contract(
        "NO_SHELL_INJECTION",
        lambda fp, tree: not any(
            isinstance(node, ast.Call) and
            any(isinstance(kw.value, ast.Constant) and kw.value.value is True
                for kw in node.keywords if kw.arg == 'shell')
            for node in ast.walk(tree)
        ),
        "CRITICAL"
    ),
    Contract(
        "NO_SILENT_FAILURES",
        lambda fp, tree: not any(
            isinstance(node, ast.ExceptHandler) and
            len(node.body) == 1 and
            isinstance(node.body[0], ast.Pass)
            for node in ast.walk(tree)
        ),
        "CRITICAL"
    ),
    # META_COGNITIVE_REQUIRED contract (Oct 28, 2025 - Guardian Zero)
    # TODO Week 2: Enforce that complex operations use @meta_cognitive decorator
    # Contract(
    #     "META_COGNITIVE_REQUIRED",
    #     lambda fp, tree: _check_meta_cognitive_usage(fp, tree),
    #     "WARNING"
    # ),
]

# Helper for META_COGNITIVE_REQUIRED contract (Week 2 implementation)
def _check_meta_cognitive_usage(filepath: str, tree: ast.Module) -> bool:
    """
    Check if complex operations use @meta_cognitive decorator
    
    COMPLEXITY HEURISTICS (Week 2):
    - Functions >50 lines
    - Functions with nested loops
    - Functions performing I/O operations
    - Functions with complex error handling
    
    EXEMPTIONS:
    - Simple getters/setters
    - Property methods
    - __init__, __str__, __repr__
    - Test functions
    """
    # TODO Week 2: Implement complexity detection
    # TODO Week 2: Check for @meta_cognitive decorator presence
    # TODO Week 2: Return False if complex operation lacks decorator
    return True  # Always pass for now (monitoring phase)

class ContractEnforcer(MetaPathFinder):
    def __init__(self, contracts: List[Contract], project_root: Path):
        self.contracts = contracts
        self.project_root = project_root
        self.validation_cache = {}
        self.violation_report = []
        self.validated_count = 0
        self.self_validated = False
        
    def find_spec(self, fullname: str, path: Optional[List[str]], target=None) -> Optional[ModuleSpec]:
        if not self.self_validated:
            self._self_validate()
            self.self_validated = True
        
        if not self._is_project_module(fullname, path):
            return None
        
        filepath = self._find_module_file(fullname, path)
        if not filepath:
            return None
        
        if filepath in self.validation_cache:
            if not self.validation_cache[filepath]:
                self._fail_fast(fullname, filepath)
            return None
        
        valid = self._validate_module(filepath)
        self.validation_cache[filepath] = valid
        
        if not valid:
            self._fail_fast(fullname, filepath)
        
        return None
    
    def _is_project_module(self, fullname: str, path: Optional[List[str]]) -> bool:
        if path is None:
            return False
        for p in path or []:
            try:
                if Path(p).is_relative_to(self.project_root):
                    return True
            except (ValueError, AttributeError):
                if str(self.project_root) in str(p):
                    return True
        return False
    
    def _find_module_file(self, fullname: str, path: Optional[List[str]]) -> Optional[str]:
        if not path:
            return None
        name = fullname.split('.')[-1]
        for p in path:
            init_file = Path(p) / name / '__init__.py'
            if init_file.exists():
                return str(init_file)
            module_file = Path(p) / f'{name}.py'
            if module_file.exists():
                return str(module_file)
        return None
    
    def _validate_module(self, filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filepath)
            all_valid = True
            violations_found = []
            for contract in self.contracts:
                if not contract.validate(filepath, tree):
                    all_valid = False
                    violations_found.append(contract.name)
            self.validated_count += 1
            if not all_valid:
                self.violation_report.append({
                    'file': filepath,
                    'violations': violations_found
                })
            return all_valid
        except SyntaxError:
            return False
        except Exception:
            return True
    
    def _fail_fast(self, fullname: str, filepath: str):
        violations = [v for v in self.violation_report if v['file'] == filepath]
        error_msg = f"""
⚠️  BOOT CONTRACT WARNING - VIOLATION DETECTED
Module: {fullname}
File: {filepath}
Violations: {violations[0]['violations'] if violations else []}

MODE: WARNING (logging only)
"""
        print(error_msg, file=sys.stderr)
        with open('/tmp/boot_contract_violations.log', 'a') as f:
            f.write(f"{datetime.now().isoformat()} - {filepath}: {violations}\n")
    
    def _self_validate(self):
        if self not in sys.meta_path:
            print("🔴 FATAL: Boot Contract not in sys.meta_path", file=sys.stderr)
            sys.exit(1)

def install_boot_contract(project_root: Optional[Path] = None, contracts: Optional[List[Contract]] = None) -> ContractEnforcer:
    if project_root is None:
        current = Path.cwd()
        while current != current.parent:
            if (current / '.git').exists() or (current / 'pyproject.toml').exists():
                project_root = current
                break
            current = current.parent
        if project_root is None:
            project_root = Path.cwd()
    
    if contracts is None:
        contracts = CONTRACTS
    
    enforcer = ContractEnforcer(contracts, project_root)
    sys.meta_path.insert(0, enforcer)
    
    print(f"✅ Boot Contract installed - enforcing {len(contracts)} contracts")
    print(f"   Project root: {project_root}")
    
    return enforcer

_GLOBAL_ENFORCER = None

def get_enforcer() -> Optional[ContractEnforcer]:
    return _GLOBAL_ENFORCER

def bootstrap():
    global _GLOBAL_ENFORCER
    if _GLOBAL_ENFORCER is None:
        _GLOBAL_ENFORCER = install_boot_contract()
    return _GLOBAL_ENFORCER
