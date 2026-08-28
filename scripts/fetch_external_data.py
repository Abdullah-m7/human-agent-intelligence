"""Fetch pinned public datasets used by the research program.

Raw third-party data are not committed to this repository. This script downloads
known files and verifies SHA-256 hashes observed at Stage 001 (2026-08-28).
"""

from __future__ import annotations

import argparse
import hashlib
import urllib.request
from pathlib import Path

SOURCES = {
    "haiid": {
        "url": "https://raw.githubusercontent.com/kailas-v/human-ai-interactions/main/haiid_dataset.csv",
        "sha256": "be9223b6bf34f996cdace9b1c0d43876df0e480bcb9322e6a7f774de0f2f0eed",
        "path": "data/external/haiid/haiid_dataset.csv",
    },
    "vaccaro_data": {
        "url": "https://osf.io/download/5vqd9/?view_only=b9e1e86079c048b4bfb03bee6966e560",
        "sha256": "9584f9a27a32c567f4763f94ec2fce0434ea3bf2233f74d49a1b0d3f26674b0b",
        "path": "data/external/vaccaro2024/Data_Extraction.csv",
    },
    "vaccaro_code": {
        "url": "https://osf.io/download/rgqsc/?view_only=b9e1e86079c048b4bfb03bee6966e560",
        "sha256": "e66ec93f15af34b27383f75e3ba58419b206e21dc3f2613ee53730cbc089697e",
        "path": "data/external/vaccaro2024/AnalysisScript_Final.Rmd",
    },
    "himmelstein_study2_jas": {
        "url": "https://osf.io/download/cjd39/",
        "sha256": "1162176e18c8414d9b51f71cfd3b61fd4755c321d7d82725c050c3cad3abf77f",
        "path": "data/external/himmelstein2023/Study_2_JAS_Data.csv",
    },
    "himmelstein_study2_demographics": {
        "url": "https://osf.io/download/bxqkf/",
        "sha256": "0e8bb7336c8f8252c04806f2ab745428202e0a6841d94746ec77d3e99814ede2",
        "path": "data/external/himmelstein2023/Study_2_demographics_and_scales.csv",
    },
    "himmelstein_study2_codebook": {
        "url": "https://osf.io/download/8y47b/",
        "sha256": "c81c329baa9dcb83588ea47bfbf8c4730dcb1f65d009e9afa9ec166caa4d82ea",
        "path": "data/external/himmelstein2023/Study_2_Codebook.xlsx",
    },
    "soleimanof_neufeld_2026": {
        "url": "https://osf.io/download/d58vx/?view_only=0c9d07bac94d4a1089588f647db735a0",
        "sha256": "660e35ae12c39823838ca2729b43362244cc9c8271aa543baa9ae9dc90d69388",
        "path": "data/external/soleimanof_neufeld_2026/Dataset.xlsx",
    },
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(name: str, root: Path, overwrite: bool = False) -> Path:
    spec = SOURCES[name]
    dest = root / spec["path"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not overwrite:
        observed = sha256(dest.read_bytes())
        if observed == spec["sha256"]:
            print(f"verified existing {name}: {dest}")
            return dest
        raise RuntimeError(f"existing {dest} has unexpected SHA-256: {observed}")
    req = urllib.request.Request(spec["url"], headers={"User-Agent": "human-agent-intelligence-research/0.1"})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = response.read()
    observed = sha256(data)
    if observed != spec["sha256"]:
        raise RuntimeError(f"hash mismatch for {name}: expected {spec['sha256']}, observed {observed}")
    dest.write_bytes(data)
    print(f"downloaded and verified {name}: {dest}")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("names", nargs="*", choices=sorted(SOURCES), default=sorted(SOURCES))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    names = args.names or sorted(SOURCES)
    for name in names:
        fetch(name, args.root, args.overwrite)


if __name__ == "__main__":
    main()
