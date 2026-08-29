"""Static validation and isolated execution for synthesized ARC programs.

Candidate code is never trusted. It is parsed and checked in the parent, then
executed by an isolated Python interpreter with a minimal builtins mapping,
resource limits, an empty temporary working directory, and a wall-clock timeout.
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Optional, Sequence


SAFE_BUILTINS = frozenset(
    {
        "abs",
        "all",
        "any",
        "bool",
        "dict",
        "divmod",
        "enumerate",
        "filter",
        "float",
        "int",
        "iter",
        "len",
        "list",
        "map",
        "max",
        "min",
        "next",
        "pow",
        "range",
        "reversed",
        "round",
        "set",
        "sorted",
        "sum",
        "tuple",
        "zip",
    }
)

SAFE_METHODS = frozenset(
    {
        "add",
        "append",
        "clear",
        "copy",
        "count",
        "difference",
        "discard",
        "extend",
        "get",
        "index",
        "insert",
        "intersection",
        "items",
        "keys",
        "pop",
        "remove",
        "reverse",
        "setdefault",
        "sort",
        "union",
        "update",
        "values",
    }
)

DANGEROUS_NAMES = frozenset(
    {
        "__import__",
        "breakpoint",
        "classmethod",
        "compile",
        "delattr",
        "dir",
        "eval",
        "exec",
        "getattr",
        "globals",
        "help",
        "input",
        "locals",
        "memoryview",
        "object",
        "open",
        "property",
        "setattr",
        "staticmethod",
        "super",
        "type",
        "vars",
    }
)

DENIED_NODES = (
    ast.AsyncFunctionDef,
    ast.Await,
    ast.ClassDef,
    ast.Global,
    ast.Import,
    ast.ImportFrom,
    ast.Lambda,
    ast.Nonlocal,
    ast.With,
    ast.AsyncWith,
    ast.Yield,
    ast.YieldFrom,
)

BRANCH_NODES = (ast.If, ast.For, ast.While, ast.IfExp, ast.comprehension)


@dataclass(frozen=True)
class SandboxPolicy:
    max_source_length: int = 12_000
    max_ast_nodes: int = 2_000
    timeout_s: float = 2.0
    max_grid_rows: int = 30
    max_grid_cols: int = 30
    memory_limit_mb: int = 512
    cpu_limit_s: int = 2


@dataclass(frozen=True)
class SourceValidation:
    valid: bool
    error: Optional[str]
    ast_node_count: int
    branch_count: int


@dataclass(frozen=True)
class ExecutionResult:
    valid: bool
    outputs: Optional[list[list[list[int]]]]
    error: Optional[str]
    elapsed_s: float


def validate_grid(grid: Any, policy: SandboxPolicy = SandboxPolicy()) -> tuple[bool, Optional[str]]:
    if not isinstance(grid, list) or not grid:
        return False, "grid_not_nonempty_list"
    if len(grid) > policy.max_grid_rows:
        return False, "too_many_rows"
    if any(not isinstance(row, list) or not row for row in grid):
        return False, "row_not_nonempty_list"
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return False, "ragged_grid"
    width = next(iter(widths))
    if width > policy.max_grid_cols:
        return False, "too_many_columns"
    for row in grid:
        for cell in row:
            if isinstance(cell, bool) or not isinstance(cell, int):
                return False, "non_integer_cell"
            if not 0 <= cell <= 9:
                return False, "color_out_of_range"
    return True, None


def validate_source(source: str, policy: SandboxPolicy = SandboxPolicy()) -> SourceValidation:
    if not isinstance(source, str) or not source.strip():
        return SourceValidation(False, "empty_source", 0, 0)
    if len(source) > policy.max_source_length:
        return SourceValidation(False, "source_too_long", 0, 0)
    try:
        tree = ast.parse(source, mode="exec")
    except SyntaxError:
        return SourceValidation(False, "syntax_error", 0, 0)

    nodes = list(ast.walk(tree))
    node_count = len(nodes)
    branch_count = sum(isinstance(node, BRANCH_NODES) for node in nodes)
    if node_count > policy.max_ast_nodes:
        return SourceValidation(False, "too_many_ast_nodes", node_count, branch_count)

    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        return SourceValidation(False, "single_top_level_function_required", node_count, branch_count)
    solve = tree.body[0]
    if solve.name != "solve":
        return SourceValidation(False, "solve_function_required", node_count, branch_count)
    if solve.decorator_list:
        return SourceValidation(False, "decorators_forbidden", node_count, branch_count)
    args = solve.args
    if (
        len(args.args) != 1
        or args.args[0].arg != "grid"
        or args.vararg is not None
        or args.kwarg is not None
        or args.kwonlyargs
        or args.defaults
        or args.kw_defaults
        or getattr(args, "posonlyargs", [])
    ):
        return SourceValidation(False, "solve_signature_must_be_grid_only", node_count, branch_count)

    local_functions = {node.name for node in nodes if isinstance(node, ast.FunctionDef)}
    for node in nodes:
        if isinstance(node, DENIED_NODES):
            return SourceValidation(False, f"forbidden_ast:{type(node).__name__}", node_count, branch_count)
        if isinstance(node, ast.Name):
            if node.id.startswith("__") or node.id in DANGEROUS_NAMES:
                return SourceValidation(False, f"forbidden_name:{node.id}", node_count, branch_count)
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("_") or node.attr not in SAFE_METHODS:
                return SourceValidation(False, f"forbidden_attribute:{node.attr}", node_count, branch_count)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id not in SAFE_BUILTINS and node.func.id not in local_functions:
                    return SourceValidation(False, f"forbidden_call:{node.func.id}", node_count, branch_count)
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr not in SAFE_METHODS:
                    return SourceValidation(False, f"forbidden_method:{node.func.attr}", node_count, branch_count)
            else:
                return SourceValidation(False, "dynamic_call_forbidden", node_count, branch_count)
        if isinstance(node, ast.Constant) and not isinstance(
            node.value, (int, float, str, bool, type(None))
        ):
            return SourceValidation(False, "forbidden_constant_type", node_count, branch_count)
    return SourceValidation(True, None, node_count, branch_count)


_WORKER = r'''
import json
import resource
import sys

payload = json.loads(sys.stdin.read())
memory = int(payload["memory_limit_mb"]) * 1024 * 1024
cpu = int(payload["cpu_limit_s"])
for key, limits in (
    ("RLIMIT_CPU", (cpu, cpu)),
    ("RLIMIT_FSIZE", (0, 0)),
    ("RLIMIT_NOFILE", (16, 16)),
    ("RLIMIT_AS", (memory, memory)),
):
    if hasattr(resource, key):
        try:
            resource.setrlimit(getattr(resource, key), limits)
        except Exception:
            pass

safe_names = payload["safe_builtins"]
original = __builtins__
if not isinstance(original, dict):
    original = original.__dict__
safe = {name: original[name] for name in safe_names}
namespace = {"__builtins__": safe}
compiled = compile(payload["source"], "<candidate>", "exec")
exec(compiled, namespace, namespace)
solve = namespace["solve"]

def valid_grid(grid):
    if not isinstance(grid, list) or not grid or len(grid) > payload["max_rows"]:
        return False
    if any(not isinstance(row, list) or not row for row in grid):
        return False
    widths = {len(row) for row in grid}
    if len(widths) != 1 or next(iter(widths)) > payload["max_cols"]:
        return False
    return all(
        isinstance(cell, int) and not isinstance(cell, bool) and 0 <= cell <= 9
        for row in grid for cell in row
    )

outputs = []
for grid in payload["grids"]:
    output = solve(grid)
    if not valid_grid(output):
        raise ValueError("invalid_output_grid")
    outputs.append(output)
sys.stdout.write(json.dumps({"outputs": outputs}, separators=(",", ":")))
'''


def execute_program(
    source: str,
    grids: Sequence[list[list[int]]],
    policy: SandboxPolicy = SandboxPolicy(),
) -> ExecutionResult:
    validation = validate_source(source, policy)
    if not validation.valid:
        return ExecutionResult(False, None, validation.error, 0.0)
    for grid in grids:
        valid, error = validate_grid(grid, policy)
        if not valid:
            return ExecutionResult(False, None, f"invalid_input:{error}", 0.0)

    payload = {
        "source": source,
        "grids": list(grids),
        "safe_builtins": sorted(SAFE_BUILTINS),
        "max_rows": policy.max_grid_rows,
        "max_cols": policy.max_grid_cols,
        "memory_limit_mb": policy.memory_limit_mb,
        "cpu_limit_s": policy.cpu_limit_s,
    }
    started = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="stage005_sandbox_") as workdir:
            completed = subprocess.run(
                [sys.executable, "-I", "-S", "-c", _WORKER],
                input=json.dumps(payload, separators=(",", ":")),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=policy.timeout_s,
                cwd=workdir,
                env={"PYTHONHASHSEED": "0"},
                close_fds=True,
                start_new_session=True,
                check=False,
            )
    except subprocess.TimeoutExpired:
        return ExecutionResult(False, None, "timeout", time.monotonic() - started)

    elapsed = time.monotonic() - started
    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()[-1] if completed.stderr.strip() else "unknown"
        return ExecutionResult(False, None, f"runtime_error:{detail[:160]}", elapsed)
    try:
        obj = json.loads(completed.stdout)
        outputs = obj["outputs"]
    except Exception:
        return ExecutionResult(False, None, "worker_protocol_error", elapsed)
    if not isinstance(outputs, list) or len(outputs) != len(grids):
        return ExecutionResult(False, None, "worker_output_count_mismatch", elapsed)
    for output in outputs:
        valid, error = validate_grid(output, policy)
        if not valid:
            return ExecutionResult(False, None, f"invalid_output:{error}", elapsed)
    return ExecutionResult(True, outputs, None, elapsed)
