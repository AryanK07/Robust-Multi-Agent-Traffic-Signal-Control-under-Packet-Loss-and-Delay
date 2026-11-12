"""Content-addressed campaigns with immutable, explicitly versioned attempts."""

import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()).hexdigest()


def write_json_exclusive(path: Path, value: Any) -> None:
    """Never replace a completed record, including during retry."""
    encoded = json.dumps(value, indent=2, sort_keys=True, allow_nan=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(encoded + "\n")


class CampaignStore:
    """One resolved design/source/checkpoint identity per output directory."""

    def __init__(self, directory: Path, manifest: dict[str, Any]) -> None:
        self.directory = directory
        self.identity = canonical_hash(manifest)
        path = directory / "manifest.json"
        if path.exists():
            if json.loads(path.read_text(encoding="utf-8")) != manifest:
                raise ValueError("Campaign identity mismatch; use a new output directory")
        else:
            if directory.exists() and any(directory.iterdir()):
                raise ValueError("Refusing to adopt an existing unversioned directory")
            write_json_exclusive(path, manifest)

    def run_id(self, specification: dict[str, Any]) -> str:
        return canonical_hash({"campaign": self.identity, "specification": specification})

    def attempts(self, specification: dict[str, Any]) -> list[dict[str, Any]]:
        run_id = self.run_id(specification)
        rows = []
        for path in sorted((self.directory / "raw" / run_id).glob("*.json")):
            row = json.loads(path.read_text(encoding="utf-8"))
            if (row["run_id"] != run_id or row["specification"] != specification
                    or path.stem != f"{row['attempt']:04d}"):
                raise ValueError(f"Corrupted attempt identity: {path}")
            rows.append(row)
        return rows

    def should_run(self, specification: dict[str, Any], retry_failed: bool = False) -> bool:
        rows = self.attempts(specification)
        if any(row["status"] == "success" for row in rows):
            return False
        return not rows or retry_failed

    def record(self, specification: dict[str, Any], status: str, payload: dict) -> dict:
        if status not in {"success", "failed"}:
            raise ValueError("status must be success or failed")
        rows = self.attempts(specification)
        if any(row["status"] == "success" for row in rows):
            raise FileExistsError("This logical run already succeeded")
        attempt = max((row["attempt"] for row in rows), default=0) + 1
        run_id = self.run_id(specification)
        row = dict(run_id=run_id, attempt=attempt, specification=specification,
                   status=status, payload=payload)
        write_json_exclusive(self.directory / "raw" / run_id / f"{attempt:04d}.json", row)
        return row

    def successful(self) -> list[dict]:
        """Return one success per logical run; failed attempts remain on disk."""
        selected = {}
        for path in sorted((self.directory / "raw").glob("*/*.json")):
            row = json.loads(path.read_text(encoding="utf-8"))
            if row["status"] == "success":
                if row["run_id"] in selected:
                    raise ValueError("Multiple successes for one logical run")
                if self.run_id(row["specification"]) != row["run_id"]:
                    raise ValueError("Result belongs to a different campaign")
                selected[row["run_id"]] = row
        return list(selected.values())
