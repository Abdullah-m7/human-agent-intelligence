#!/usr/bin/env python3
"""Stage 004 generative-LLM ARC adapter with a sealed evaluation firewall.

The model never receives test outputs. Autonomy is certified by reconstructing
one hash-selected hidden training demonstration (HDC) in a separate call.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib import error, request

REPO = Path(__file__).resolve().parents[1]
SPLIT_FILE = REPO / "benchmarks" / "capability_twin" / "stage004_split.json"
LOCK_FILE = REPO / "papers" / "01_agentic_bottleneck" / "STAGE004_CONFIRMATORY_LOCK_V1.md"
DEFAULT_DATA = Path("/tmp/CogARC-dataRepository/Task JSONs")
MAX_TOKENS = 120

SYSTEM_PROMPT = (
    "You are a precise ARC grid-transformation solver. Infer the transformation "
    "from the provided training pairs and apply it to the target input. "
    "Return only the requested compact grid encoding; do not explain."
)
USER_TEMPLATE = (
    "TRAINING_PAIRS={training}\n"
    "TARGET_INPUT={target}\n"
    "Return JSON exactly as {{\"grid\":\"r1c1,r1c2; r2c1,r2c2\"}}. "
    "Rows are separated by semicolons, cells by commas, and every cell must be a single integer 0-9."
)
RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "arc_grid_compact",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "grid": {
                    "type": "string",
                    "pattern": "^[0-9](,[0-9])*(;[0-9](,[0-9])*)*$",
                }
            },
            "required": ["grid"],
            "additionalProperties": False,
        },
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def contract_hashes() -> Dict[str, str]:
    return {
        "split_sha256": sha256_bytes(SPLIT_FILE.read_bytes()),
        "system_prompt_sha256": sha256_bytes(SYSTEM_PROMPT.encode("utf-8")),
        "user_template_sha256": sha256_bytes(USER_TEMPLATE.encode("utf-8")),
        "response_format_sha256": sha256_bytes(canonical_json(RESPONSE_FORMAT).encode("utf-8")),
    }


def hdc_index(task_id: str, n_train: int) -> int:
    if n_train <= 0:
        raise ValueError("n_train must be positive")
    return int(hashlib.sha256(task_id.encode("utf-8")).hexdigest(), 16) % n_train


def strip_test_outputs(task: Dict[str, Any]) -> Dict[str, Any]:
    """Return a model-visible task object. This function is intentionally tiny/auditable."""
    return {
        "train": [{"input": x["input"], "output": x["output"]} for x in task["train"]],
        "test": [{"input": x["input"]} for x in task["test"]],
    }


def compact_prompt(training: Sequence[Dict[str, Any]], target: List[List[int]]) -> str:
    return USER_TEMPLATE.format(training=canonical_json(list(training)), target=canonical_json(target))


def parse_compact_grid(content: str) -> Tuple[Optional[List[List[int]]], Optional[str]]:
    try:
        obj = json.loads(content)
    except Exception:
        m = re.search(r"\{.*?\}", content, flags=re.S)
        if not m:
            return None, "json_parse"
        try:
            obj = json.loads(m.group(0))
        except Exception:
            return None, "json_parse"
    raw = obj.get("grid") if isinstance(obj, dict) else None
    if not isinstance(raw, str) or not raw.strip():
        return None, "missing_grid"
    rows: List[List[int]] = []
    for row in raw.strip().split(";"):
        row = row.strip()
        if not row:
            return None, "empty_row"
        cells = [x.strip() for x in row.split(",")]
        if not cells or any(not re.fullmatch(r"[0-9]", x) for x in cells):
            return None, "bad_cell"
        rows.append([int(x) for x in cells])
    widths = {len(r) for r in rows}
    if len(widths) != 1:
        return None, "ragged"
    return rows, None


@dataclass
class CallResult:
    grid: Optional[List[List[int]]]
    parse_error: Optional[str]
    content_sha256: str
    prompt_sha256: str
    latency_s: float
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    finish_reason: Optional[str]


class OpenAICompatClient:
    def __init__(self, base_url: str, model: str, temperature: float, seed: int, timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.seed = seed
        self.timeout = timeout

    def infer(
        self,
        training: Sequence[Dict[str, Any]],
        target: List[List[int]],
        seed_offset: int = 0,
    ) -> CallResult:
        user = compact_prompt(training, target)
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature,
            "seed": self.seed + seed_offset,
            "max_tokens": MAX_TOKENS,
            "response_format": RESPONSE_FORMAT,
        }
        payload = canonical_json(body).encode("utf-8")
        req = request.Request(
            self.base_url + "/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        t0 = time.time()
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                decoded = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        latency = time.time() - t0
        choice = decoded["choices"][0]
        content = choice["message"].get("content", "") or ""
        grid, parse_error = parse_compact_grid(content)
        usage = decoded.get("usage", {})
        return CallResult(
            grid=grid,
            parse_error=parse_error,
            content_sha256=sha256_bytes(content.encode("utf-8")),
            prompt_sha256=sha256_bytes(payload),
            latency_s=round(latency, 6),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            finish_reason=choice.get("finish_reason"),
        )


def lock_status(text: str) -> Optional[str]:
    """Return the unique LOCK_STATUS value from an exact standalone status line."""
    values: List[str] = []
    for line in text.splitlines():
        m = re.fullmatch(r"\s*LOCK_STATUS:\s*([A-Z0-9_]+)\s*", line)
        if m:
            values.append(m.group(1))
    if len(values) > 1:
        raise ValueError("confirmatory lock contains multiple LOCK_STATUS lines")
    return values[0] if values else None


def assert_phase_allowed(phase: str) -> None:
    if phase != "eval":
        return
    if not LOCK_FILE.exists():
        raise SystemExit(
            "SEALED: evaluation requires papers/01_agentic_bottleneck/"
            "STAGE004_CONFIRMATORY_LOCK_V1.md committed before first eval query"
        )
    try:
        status = lock_status(LOCK_FILE.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise SystemExit(f"SEALED: invalid confirmatory lock: {exc}") from exc
    if status != "LOCKED":
        raise SystemExit("SEALED: confirmatory lock status line is not exactly LOCKED")


def assert_eval_scope(phase: str, limit: Optional[int], only: Optional[Sequence[str]]) -> None:
    """Confirmatory eval must address the entire sealed split; only deterministic resume may be partial."""
    if phase == "eval" and (limit is not None or only):
        raise SystemExit("SEALED: --limit and --only are development-only; eval always targets all sealed tasks")


def participant_target(task: Dict[str, Any]) -> Dict[str, Any]:
    """CogARC participant-visible query; raw ARC extras are not behavioral targets."""
    return task["test"][0]


def load_task(data_dir: Path, task_id: str) -> Dict[str, Any]:
    task = json.loads((data_dir / f"{task_id}.json").read_text(encoding="utf-8"))
    if not task.get("train") or not task.get("test"):
        raise ValueError(f"Malformed ARC task: {task_id}")
    visible = strip_test_outputs(task)
    if any("output" in x for x in visible["test"]):
        raise AssertionError("Leak guard failed")
    return task


def run_task(client: OpenAICompatClient, task_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
    # Production is aligned to the participant-visible CogARC target test[0].
    target = participant_target(task)
    production = client.infer(task["train"], target["input"], seed_offset=0)

    # HDC hides one complete demonstration and uses only its input as the target.
    idx = hdc_index(task_id, len(task["train"]))
    cert_target = task["train"][idx]
    cert_training = [x for j, x in enumerate(task["train"]) if j != idx]
    certificate = client.infer(cert_training, cert_target["input"], seed_offset=100003)

    prod_valid = production.grid is not None
    hdc_valid = certificate.grid is not None
    prod_correct = bool(prod_valid and production.grid == target["output"])
    hdc_correct = bool(hdc_valid and certificate.grid == cert_target["output"])
    act = bool(prod_valid and hdc_correct)
    return {
        "task_id": task_id,
        "source_n_test_queries": len(task["test"]),
        "participant_target_index": 0,
        "hdc_index": idx,
        "production_valid": prod_valid,
        "production_correct": prod_correct,
        "hdc_valid": hdc_valid,
        "hdc_correct": hdc_correct,
        "act": act,
        "wrong_act": bool(act and not prod_correct),
        "production_parse_error": production.parse_error,
        "hdc_parse_error": certificate.parse_error,
        "production_prompt_sha256": production.prompt_sha256,
        "hdc_prompt_sha256": certificate.prompt_sha256,
        "production_content_sha256": production.content_sha256,
        "hdc_content_sha256": certificate.content_sha256,
        "production_latency_s": production.latency_s,
        "hdc_latency_s": certificate.latency_s,
        "production_prompt_tokens": production.prompt_tokens,
        "production_completion_tokens": production.completion_tokens,
        "hdc_prompt_tokens": certificate.prompt_tokens,
        "hdc_completion_tokens": certificate.completion_tokens,
        "production_finish_reason": production.finish_reason,
        "hdc_finish_reason": certificate.finish_reason,
    }


def summarize(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(rows)
    acts = sum(bool(r["act"]) for r in rows)
    correct = sum(bool(r["production_correct"]) for r in rows)
    wrong_acts = sum(bool(r["wrong_act"]) for r in rows)
    correct_acts = sum(bool(r["act"] and r["production_correct"]) for r in rows)
    return {
        "n_tasks": n,
        "standalone_accuracy": correct / n if n else None,
        "act_coverage": acts / n if n else None,
        "act_precision": correct_acts / acts if acts else None,
        "unsafe_autonomy_mass": wrong_acts / n if n else None,
        "n_acts": acts,
        "n_wrong_acts": wrong_acts,
        "hdc_pass_rate": sum(bool(r["hdc_correct"]) for r in rows) / n if n else None,
        "production_parse_rate": sum(bool(r["production_valid"]) for r in rows) / n if n else None,
        "hdc_parse_rate": sum(bool(r["hdc_valid"]) for r in rows) / n if n else None,
    }


def expected_row_contract(
    phase: str,
    model: str,
    model_label: str,
    temperature: float,
    seed: int,
) -> Dict[str, Any]:
    return {
        "phase": phase,
        "model": model,
        "model_label": model_label,
        "temperature": temperature,
        "seed": seed,
        "participant_target_index": 0,
        "max_tokens": MAX_TOKENS,
        **contract_hashes(),
    }


def validate_resume_row(row: Dict[str, Any], expected: Dict[str, Any], allowed_task_ids: Sequence[str]) -> None:
    if row.get("task_id") not in set(allowed_task_ids):
        raise ValueError(f"resume row task outside fixed phase split: {row.get('task_id')}")
    mismatches = {
        key: (row.get(key), value)
        for key, value in expected.items()
        if row.get(key) != value
    }
    if mismatches:
        parts = ", ".join(f"{k}: row={got!r} current={want!r}" for k, (got, want) in mismatches.items())
        raise ValueError(f"resume provenance mismatch: {parts}")


def load_resume_rows(
    rows_file: Path,
    expected: Dict[str, Any],
    allowed_task_ids: Sequence[str],
) -> List[Dict[str, Any]]:
    if not rows_file.exists():
        return []
    rows: List[Dict[str, Any]] = []
    seen = set()
    for line_no, line in enumerate(rows_file.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        validate_resume_row(row, expected, allowed_task_ids)
        task_id = row["task_id"]
        if task_id in seen:
            raise ValueError(f"duplicate resume row for task {task_id} at line {line_no}")
        seen.add(task_id)
        rows.append(row)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["dev", "eval"], required=True)
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--model-label", required=True)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=240829)
    ap.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--out-dir", type=Path, default=REPO / "results" / "stage004_llm_hdc")
    args = ap.parse_args()

    assert_phase_allowed(args.phase)
    assert_eval_scope(args.phase, args.limit, args.only)

    split = json.loads(SPLIT_FILE.read_text(encoding="utf-8"))
    key = "development_tasks" if args.phase == "dev" else "evaluation_tasks"
    allowed = list(split[key])
    if args.only:
        unknown = sorted(set(args.only) - set(allowed))
        if unknown:
            raise SystemExit(f"Refusing tasks outside {args.phase} split: {unknown}")
        task_ids = [x for x in allowed if x in set(args.only)]
    else:
        task_ids = allowed
    if args.limit is not None:
        task_ids = task_ids[: args.limit]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows_file = args.out_dir / f"{args.phase}_{args.model_label}_rows.jsonl"
    summary_file = args.out_dir / f"{args.phase}_{args.model_label}_summary.json"
    client = OpenAICompatClient(args.base_url, args.model, args.temperature, args.seed)

    expected = expected_row_contract(
        args.phase,
        args.model,
        args.model_label,
        args.temperature,
        args.seed,
    )
    try:
        rows = load_resume_rows(rows_file, expected, allowed)
    except (ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"REFUSING RESUME: {exc}") from exc
    done = {r["task_id"] for r in rows}

    hashes = contract_hashes()
    for i, task_id in enumerate(task_ids, 1):
        if task_id in done:
            continue
        task = load_task(args.data_dir, task_id)
        row = run_task(client, task_id, task)
        row.update({
            "phase": args.phase,
            "model": args.model,
            "model_label": args.model_label,
            "temperature": args.temperature,
            "seed": args.seed,
            **hashes,
            "max_tokens": MAX_TOKENS,
        })
        with rows_file.open("a", encoding="utf-8") as fh:
            fh.write(canonical_json(row) + "\n")
        rows.append(row)
        s = summarize(rows)
        print(
            f"[{i}/{len(task_ids)}] {task_id} prod={int(row['production_correct'])} "
            f"hdc={int(row['hdc_correct'])} act={int(row['act'])} wrong_act={int(row['wrong_act'])} "
            f"running_acc={s['standalone_accuracy']:.3f} act_cov={s['act_coverage']:.3f}",
            flush=True,
        )

    selected = [r for r in rows if r["task_id"] in set(task_ids)]
    summary = summarize(selected)
    summary.update({
        "phase": args.phase,
        "model": args.model,
        "model_label": args.model_label,
        "temperature": args.temperature,
        "seed": args.seed,
        "task_ids": task_ids,
        **hashes,
        "max_tokens": MAX_TOKENS,
    })
    summary_file.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
