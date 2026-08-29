"""Verifier-bounded program-synthesis agent for Stage 005."""

from .agent import BUDGETS, BASE_SEED, seed_for_candidate
from .candidate import CandidateEvaluation, evaluate_candidate, select_best
from .sandbox import SandboxPolicy, execute_program, validate_grid, validate_source

__all__ = [
    "BASE_SEED",
    "BUDGETS",
    "CandidateEvaluation",
    "SandboxPolicy",
    "evaluate_candidate",
    "execute_program",
    "seed_for_candidate",
    "select_best",
    "validate_grid",
    "validate_source",
]
