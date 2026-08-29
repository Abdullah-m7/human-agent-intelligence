import unittest

from src.program_agent.sandbox import SandboxPolicy, execute_program, validate_grid, validate_source


class Stage005SandboxTests(unittest.TestCase):
    def test_conventional_underscore_local_is_safe(self):
        source = "def solve(grid):\n    out = []\n    for _ in range(1):\n        out = [row[:] for row in grid]\n    return out"
        self.assertTrue(validate_source(source).valid)

    def test_dunder_name_is_rejected(self):
        source = "def solve(grid):\n    __builtins__ = {}\n    return grid"
        result = validate_source(source)
        self.assertFalse(result.valid)
        self.assertEqual(result.error, "forbidden_name:__builtins__")

    def test_safe_program_executes_in_isolated_worker(self):
        source = "def solve(grid):\n    return [list(row) for row in zip(*grid)]"
        result = execute_program(source, [[[1, 2], [3, 4]]])
        self.assertTrue(result.valid, result.error)
        self.assertEqual(result.outputs, [[[1, 3], [2, 4]]])

    def test_import_is_rejected(self):
        result = validate_source("def solve(grid):\n    import os\n    return grid")
        self.assertFalse(result.valid)
        self.assertIn("Import", result.error)

    def test_filesystem_open_is_rejected(self):
        result = validate_source("def solve(grid):\n    open('/tmp/x')\n    return grid")
        self.assertFalse(result.valid)
        self.assertIn("open", result.error)

    def test_dynamic_import_is_rejected(self):
        result = validate_source("def solve(grid):\n    return __import__('os')")
        self.assertFalse(result.valid)
        self.assertIn("__import__", result.error)

    def test_exec_is_rejected(self):
        result = validate_source("def solve(grid):\n    exec('x=1')\n    return grid")
        self.assertFalse(result.valid)
        self.assertIn("exec", result.error)

    def test_reflection_attribute_is_rejected(self):
        result = validate_source("def solve(grid):\n    return grid.__class__")
        self.assertFalse(result.valid)
        self.assertIn("__class__", result.error)

    def test_infinite_loop_times_out(self):
        source = "def solve(grid):\n    while True:\n        pass\n    return grid"
        policy = SandboxPolicy(timeout_s=0.25, cpu_limit_s=1)
        result = execute_program(source, [[[1]]], policy)
        self.assertFalse(result.valid)
        self.assertEqual(result.error, "timeout")

    def test_invalid_grid_shapes_and_cells_are_rejected(self):
        for grid in ([], [[1], [1, 2]], [[10]], [[True]], [[1.0]]):
            valid, _ = validate_grid(grid)
            self.assertFalse(valid, grid)

    def test_program_returning_invalid_grid_is_invalid(self):
        source = "def solve(grid):\n    return [[10]]"
        result = execute_program(source, [[[1]]])
        self.assertFalse(result.valid)
        self.assertIn("invalid_output_grid", result.error)

    def test_source_length_limit_is_enforced(self):
        source = "def solve(grid):\n    return grid\n" + ("#x" * 100)
        result = validate_source(source, SandboxPolicy(max_source_length=40))
        self.assertFalse(result.valid)
        self.assertEqual(result.error, "source_too_long")


if __name__ == "__main__":
    unittest.main()
