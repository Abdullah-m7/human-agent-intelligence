"""Stage-005 CogARC confirmatory execution firewall.

This module deliberately reads only the frozen lock, Git metadata, and the
Stage-004 ID split.  It never opens CogARC task payloads or human outcomes.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .agent import BASE_SEED, MAX_TOKENS, TEMPERATURE, TOP_P, canonical_json, contract_hashes
from .sandbox import SandboxPolicy


REPO = Path(__file__).resolve().parents[2]
LOCK_FILE = REPO / "papers" / "01_agentic_bottleneck" / "STAGE005_COGARC_CONFIRMATORY_LOCK_V1.md"
COGARC_SPLIT_FILE = REPO / "benchmarks" / "capability_twin" / "stage004_split.json"
CALIBRATION_PROVENANCE_FILE = (
    REPO / "results" / "stage005_program_synthesis" / "calibration" / "provenance.json"
)

LOCK_BEGIN = "BEGIN_STAGE005_COGARC_LOCK_FIELDS"
LOCK_END = "END_STAGE005_COGARC_LOCK_FIELDS"
CONFIRMATORY_PHASE = "cogarc-confirmatory"
COGARC_SOURCE_COMMIT = "1a319935b803580fcbd6ff002195df86a7e90095"
CALIBRATION_HEAD = "0dc1a1678f512f6ed49033551bf55dcff62739c3"
CALIBRATION_CONTRACT_COMMIT = "fa9f83c12b8c070e4799636f68ce35ab21118e33"
MODEL_NAME = "Gemma-4-26B-A4B Q4_K_M"
MODEL_API_NAME = "gemma4-26b-a4b"
MODEL_LABEL = "gemma4-26b-a4b-q4km"
MODEL_SHA256 = "b8707e57f676d8dd1b80f623b45200cc92e6966b0e95275e606f412095a49fde"
LLAMA_CPP_BUILD = "llama.cpp version 1 (9ee9a1c); AppleClang 17.0.0.17000013; Darwin arm64"
CTX_SIZE = 16_384
LOW_BUDGET = 1
HIGH_BUDGET = 8
TARGET_INDEX = 0
BOOTSTRAP_LABEL = "stage005-cogarc-task-bootstrap-v1"
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = int.from_bytes(hashlib.sha256(BOOTSTRAP_LABEL.encode()).digest()[:8], "big")
HUMAN_LEVERAGE_SPLITS = 300
HUMAN_LEVERAGE_TASKS_PER_HALF = 30
HUMAN_LEVERAGE_MIN_CAPABILITY_TRIALS = 20
HUMAN_LEVERAGE_MIN_EVALUATION_TRIALS = 20
RANKING_ACT_CONTRACT = (
    "valid_candidates_only|max_visible_train_exact_fit|tie_earliest_candidate|"
    "act_iff_selected_visible_train_exact_fit_eq_1|invalid_prediction_wrong"
)

# Commit B may change only the lock file.  Every executable contract path must
# remain byte-identical to Commit A recorded as CONTRACT_COMMIT.
CONTRACT_CODE_PATHS = (
    "src/program_agent/agent.py",
    "src/program_agent/candidate.py",
    "src/program_agent/sandbox.py",
    "src/program_agent/confirmatory.py",
    "analysis/stage005_program_synthesis.py",
    "analysis/stage005_cogarc_confirmatory.py",
    "analysis/stage005_program_ambiguity.py",
    "benchmarks/capability_twin/stage004_split.json",
)


class ConfirmatoryAbort(RuntimeError):
    """A fail-closed confirmatory contract violation."""


@dataclass(frozen=True)
class ConfirmatoryGate:
    fields: dict[str, str]
    task_ids: tuple[str, ...]
    lock_sha256: str
    lock_commit: str | None = None


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def parse_lock_text(text: str) -> dict[str, str]:
    """Parse exactly one machine block; prose cannot freeze the lock."""
    lines = text.splitlines()
    if lines.count(LOCK_BEGIN) != 1 or lines.count(LOCK_END) != 1:
        raise ConfirmatoryAbort("ABORT: lock must contain exactly one machine field block")
    start = lines.index(LOCK_BEGIN)
    end = lines.index(LOCK_END)
    if end <= start:
        raise ConfirmatoryAbort("ABORT: malformed lock field block")
    fields: dict[str, str] = {}
    pattern = re.compile(r"^([A-Z][A-Z0-9_]*): ([^\r\n]+)$")
    for line in lines[start + 1 : end]:
        match = pattern.fullmatch(line)
        if not match:
            raise ConfirmatoryAbort(f"ABORT: non-canonical lock field line: {line!r}")
        key, value = match.groups()
        if key in fields:
            raise ConfirmatoryAbort(f"ABORT: duplicate lock field: {key}")
        fields[key] = value
    return fields


def load_lock(path: Path = LOCK_FILE) -> tuple[dict[str, str], str]:
    raw = path.read_bytes()
    try:
        fields = parse_lock_text(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ConfirmatoryAbort("ABORT: lock is not UTF-8") from exc
    return fields, sha256_bytes(raw)


def load_confirmatory_ids(path: Path = COGARC_SPLIT_FILE) -> list[str]:
    """Read IDs only from the historical split; never dereference task files."""
    split = json.loads(path.read_text(encoding="utf-8"))
    evaluation = list(split.get("evaluation_tasks", []))
    development = list(split.get("development_tasks", []))
    if len(evaluation) != 60 or len(evaluation) != len(set(evaluation)):
        raise ConfirmatoryAbort("ABORT: CogARC evaluation split must contain 60 unique IDs")
    if set(evaluation) & set(development):
        raise ConfirmatoryAbort("ABORT: CogARC development/evaluation IDs overlap")
    return evaluation


def _calibration_provenance(path: Path = CALIBRATION_PROVENANCE_FILE) -> dict[str, Any]:
    provenance = json.loads(path.read_text(encoding="utf-8"))
    if provenance.get("contract_commit") != CALIBRATION_CONTRACT_COMMIT:
        raise ConfirmatoryAbort("ABORT: historical calibration provenance commit mismatch")
    return provenance


def sandbox_contract_sha256(policy: SandboxPolicy = SandboxPolicy()) -> str:
    return canonical_sha256(asdict(policy))


def expected_lock_fields() -> dict[str, str]:
    ids = load_confirmatory_ids()
    provenance = _calibration_provenance()
    hashes = contract_hashes()
    server_args = str(provenance.get("server_args", ""))
    expected = {
        "CALIBRATION_HEAD": CALIBRATION_HEAD,
        "CALIBRATION_CONTRACT_COMMIT": CALIBRATION_CONTRACT_COMMIT,
        "MODEL": MODEL_NAME,
        "MODEL_API_NAME": MODEL_API_NAME,
        "MODEL_LABEL": MODEL_LABEL,
        "MODEL_SHA256": MODEL_SHA256,
        "SYSTEM_PROMPT_SHA256": hashes["system_prompt_sha256"],
        "USER_TEMPLATE_SHA256": hashes["user_template_sha256"],
        "RESPONSE_CONTRACT_SHA256": hashes["response_contract_sha256"],
        "SANDBOX_CONTRACT_SHA256": sandbox_contract_sha256(),
        "RANKING_ACT_CONTRACT_SHA256": sha256_bytes(RANKING_ACT_CONTRACT.encode("utf-8")),
        "TEMPERATURE": str(TEMPERATURE),
        "TOP_P": str(TOP_P),
        "MAX_TOKENS": str(MAX_TOKENS),
        "BASE_SEED": str(BASE_SEED),
        "CANDIDATE_SEQUENCE": "1,2,3,4,5,6,7,8",
        "LOW_BUDGET": str(LOW_BUDGET),
        "HIGH_BUDGET": str(HIGH_BUDGET),
        "CTX_SIZE": str(CTX_SIZE),
        "LLAMA_CPP_BUILD": LLAMA_CPP_BUILD,
        "SERVER_ARGS_SHA256": sha256_bytes(server_args.encode("utf-8")),
        "COGARC_SOURCE_COMMIT": COGARC_SOURCE_COMMIT,
        "COGARC_EVAL_IDS_COUNT": str(len(ids)),
        "COGARC_EVAL_IDS_SHA256": canonical_sha256(ids),
        "TARGET_INDEX": str(TARGET_INDEX),
        "PRIMARY_RECEIVER": "ONE_SHOT",
        "PRIMARY_WEIGHTING": "TASK_BALANCED",
        "ROBUSTNESS_RECEIVERS": (
            "PARTICIPANT_WEIGHTED_ONE_SHOT,TASK_BALANCED_RETRY3,"
            "PARTICIPANT_WEIGHTED_RETRY3"
        ),
        "BOOTSTRAP_RESAMPLES": str(BOOTSTRAP_RESAMPLES),
        "BOOTSTRAP_LABEL": BOOTSTRAP_LABEL,
        "BOOTSTRAP_SEED": str(BOOTSTRAP_SEED),
        "HUMAN_LEVERAGE_SPLITS": str(HUMAN_LEVERAGE_SPLITS),
        "HUMAN_LEVERAGE_TASKS_PER_HALF": str(HUMAN_LEVERAGE_TASKS_PER_HALF),
        "HUMAN_LEVERAGE_MIN_CAPABILITY_TRIALS": str(
            HUMAN_LEVERAGE_MIN_CAPABILITY_TRIALS
        ),
        "HUMAN_LEVERAGE_MIN_EVALUATION_TRIALS": str(
            HUMAN_LEVERAGE_MIN_EVALUATION_TRIALS
        ),
    }
    historical = {
        "model_file_sha256": MODEL_SHA256,
        "system_prompt_sha256": expected["SYSTEM_PROMPT_SHA256"],
        "user_template_sha256": expected["USER_TEMPLATE_SHA256"],
        "response_contract_sha256": expected["RESPONSE_CONTRACT_SHA256"],
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "max_tokens": MAX_TOKENS,
        "base_seed": BASE_SEED,
        "llama_cpp_build": LLAMA_CPP_BUILD,
    }
    mismatches = {
        key: (provenance.get(key), value)
        for key, value in historical.items()
        if provenance.get(key) != value
    }
    if mismatches:
        raise ConfirmatoryAbort(f"ABORT: calibration provenance drift: {mismatches}")
    if canonical_sha256(provenance.get("sandbox_policy")) != expected["SANDBOX_CONTRACT_SHA256"]:
        raise ConfirmatoryAbort("ABORT: calibration sandbox provenance drift")
    return expected


def validate_lock_fields(fields: Mapping[str, str], *, require_frozen: bool = True) -> None:
    expected = expected_lock_fields()
    required = {"LOCK_STATUS", "CONTRACT_COMMIT", *expected}
    if set(fields) != required:
        missing = sorted(required - set(fields))
        extra = sorted(set(fields) - required)
        raise ConfirmatoryAbort(f"ABORT: lock field set mismatch; missing={missing}, extra={extra}")
    if require_frozen and fields["LOCK_STATUS"] != "FROZEN":
        raise ConfirmatoryAbort("ABORT: exact standalone LOCK_STATUS: FROZEN is required")
    if not require_frozen and fields["LOCK_STATUS"] not in {"DRAFT_DO_NOT_RUN", "FROZEN"}:
        raise ConfirmatoryAbort("ABORT: invalid LOCK_STATUS")
    if not re.fullmatch(r"[0-9a-f]{40}", fields["CONTRACT_COMMIT"]):
        if require_frozen:
            raise ConfirmatoryAbort("ABORT: CONTRACT_COMMIT is not a frozen Git SHA")
    mismatches = {
        key: (fields.get(key), value)
        for key, value in expected.items()
        if fields.get(key) != value
    }
    if mismatches:
        raise ConfirmatoryAbort(f"ABORT: confirmatory lock mismatch: {mismatches}")


def validate_full_task_set(requested: Sequence[str], frozen: Sequence[str]) -> None:
    if list(requested) != list(frozen):
        raise ConfirmatoryAbort("ABORT: partial, reordered, skipped, or substituted CogARC task set")


def _git_show(commit: str, path: str) -> bytes:
    try:
        return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=REPO)
    except subprocess.CalledProcessError as exc:
        raise ConfirmatoryAbort(f"ABORT: cannot resolve contract path {path} at {commit}") from exc


def validate_contract_tree(contract_commit: str) -> None:
    for rel in CONTRACT_CODE_PATHS:
        current_path = REPO / rel
        if not current_path.is_file():
            raise ConfirmatoryAbort(f"ABORT: missing executable contract path: {rel}")
        if current_path.read_bytes() != _git_show(contract_commit, rel):
            raise ConfirmatoryAbort(f"ABORT: executable contract drift after Commit A: {rel}")


def validate_lock_commit_structure(lock_path: Path, contract_commit: str) -> str:
    try:
        rel = str(lock_path.resolve().relative_to(REPO.resolve()))
    except ValueError as exc:
        raise ConfirmatoryAbort("ABORT: confirmatory lock must be inside the repository") from exc
    if lock_path.resolve() != LOCK_FILE.resolve():
        raise ConfirmatoryAbort("ABORT: only the canonical confirmatory lock path is executable")
    try:
        lock_commit = subprocess.check_output(
            ["git", "log", "-1", "--format=%H", "--", rel], cwd=REPO, text=True
        ).strip()
        parent = subprocess.check_output(
            ["git", "rev-parse", f"{lock_commit}^"], cwd=REPO, text=True
        ).strip()
        changed = subprocess.check_output(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", lock_commit],
            cwd=REPO,
            text=True,
        ).splitlines()
        subprocess.check_call(
            ["git", "merge-base", "--is-ancestor", lock_commit, "HEAD"],
            cwd=REPO,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ConfirmatoryAbort("ABORT: frozen lock commit provenance is invalid") from exc
    if parent != contract_commit:
        raise ConfirmatoryAbort("ABORT: Commit B parent is not the frozen CONTRACT_COMMIT")
    if changed != [rel]:
        raise ConfirmatoryAbort("ABORT: Commit B must change the lock file only")
    if lock_path.read_bytes() != _git_show(lock_commit, rel):
        raise ConfirmatoryAbort("ABORT: working lock bytes differ from Commit B")
    return lock_commit


def validate_source_checkout(cogarc_root: Path, expected_commit: str = COGARC_SOURCE_COMMIT) -> None:
    try:
        actual = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=cogarc_root, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ConfirmatoryAbort("ABORT: CogARC source checkout provenance unavailable") from exc
    if actual != expected_commit:
        raise ConfirmatoryAbort(
            f"ABORT: CogARC source commit mismatch: actual={actual}, expected={expected_commit}"
        )


def validate_execution_lock(
    lock_path: Path = LOCK_FILE,
    *,
    requested_task_ids: Sequence[str] | None = None,
    check_contract_tree: bool = True,
) -> ConfirmatoryGate:
    fields, lock_sha = load_lock(lock_path)
    validate_lock_fields(fields, require_frozen=True)
    task_ids = load_confirmatory_ids()
    validate_full_task_set(task_ids if requested_task_ids is None else requested_task_ids, task_ids)
    lock_commit = None
    if check_contract_tree:
        validate_contract_tree(fields["CONTRACT_COMMIT"])
        lock_commit = validate_lock_commit_structure(lock_path, fields["CONTRACT_COMMIT"])
    return ConfirmatoryGate(
        fields=dict(fields),
        task_ids=tuple(task_ids),
        lock_sha256=lock_sha,
        lock_commit=lock_commit,
    )


def validate_runtime_arguments(
    gate: ConfirmatoryGate,
    *,
    model: str,
    model_label: str,
    model_sha256: str,
    source_commit: str,
    llama_cpp_build: str,
    server_args: str,
    max_candidates: int,
    limit: int | None,
    contract_commit: str,
) -> None:
    supplied = {
        "MODEL_API_NAME": model,
        "MODEL_LABEL": model_label,
        "MODEL_SHA256": model_sha256,
        "COGARC_SOURCE_COMMIT": source_commit,
        "LLAMA_CPP_BUILD": llama_cpp_build,
        "SERVER_ARGS_SHA256": sha256_bytes(server_args.encode("utf-8")),
        "HIGH_BUDGET": str(max_candidates),
        "CONTRACT_COMMIT": contract_commit,
    }
    mismatches = {
        key: (value, gate.fields[key])
        for key, value in supplied.items()
        if value != gate.fields[key]
    }
    if mismatches:
        raise ConfirmatoryAbort(f"ABORT: runtime contract mismatch: {mismatches}")
    if limit is not None:
        raise ConfirmatoryAbort("ABORT: --limit is forbidden in confirmatory mode")


def confirmatory_row_provenance(gate: ConfirmatoryGate) -> dict[str, Any]:
    return {
        "confirmatory_lock_sha256": gate.lock_sha256,
        "cogarc_eval_ids_sha256": gate.fields["COGARC_EVAL_IDS_SHA256"],
        "cogarc_eval_ids_count": int(gate.fields["COGARC_EVAL_IDS_COUNT"]),
        "cogarc_source_commit": gate.fields["COGARC_SOURCE_COMMIT"],
        "target_index": TARGET_INDEX,
        "selected_pair": [LOW_BUDGET, HIGH_BUDGET],
        "primary_receiver": gate.fields["PRIMARY_RECEIVER"],
        "primary_weighting": gate.fields["PRIMARY_WEIGHTING"],
        "execution_contract_commit": gate.fields["CONTRACT_COMMIT"],
        "confirmatory_lock_commit": gate.lock_commit,
        "ranking_act_contract_sha256": gate.fields["RANKING_ACT_CONTRACT_SHA256"],
    }
