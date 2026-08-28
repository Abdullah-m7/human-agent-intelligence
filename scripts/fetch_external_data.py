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
