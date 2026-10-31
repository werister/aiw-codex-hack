#!/usr/bin/env python3
"""Verify Blender exports, then publish the web scene's three GLBs and manifest.

Run from any directory:
  python3 tools/blender/publish_web_assets.py --dry-run
  python3 tools/blender/publish_web_assets.py
  python3 tools/blender/publish_web_assets.py --check

The native verifier records hashes for the three GLBs used by the browser.
Every source is checked before publication, then each staged file is atomically
renamed into place. The manifest is copied byte-for-byte from the verified
asset package; verification.json does not currently record a manifest hash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = REPO_ROOT / "assets" / "airport"
EXPORT_ROOT = ASSET_ROOT / "exports"
WEB_ROOT = REPO_ROOT / "web" / "public" / "models" / "airport"
VERIFICATION_FILE = ASSET_ROOT / "verification.json"
MANIFEST_FILE = ASSET_ROOT / "manifest.json"

GLB_ASSETS = (
    "airport-environment.glb",
    "aircraft-narrowbody.glb",
    "aircraft-widebody.glb",
)
PUBLISHED_FILES = (*GLB_ASSETS, "manifest.json")


class PublishError(RuntimeError):
    """A source package or target does not satisfy the publish contract."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PublishError(f"Cannot read {path}: {error}") from error
    if not isinstance(value, dict):
        raise PublishError(f"Expected a JSON object in {path}")
    return value


def verify_manifest() -> bytes:
    try:
        raw = MANIFEST_FILE.read_bytes()
        manifest = json.loads(raw)
    except (OSError, json.JSONDecodeError) as error:
        raise PublishError(f"Cannot read airport manifest: {error}") from error
    if not isinstance(manifest, dict) or manifest.get("version") != 2:
        raise PublishError("Airport manifest must be version 2")
    if manifest.get("fps") != 60 or manifest.get("rendering", {}).get("native_fps") != 60:
        raise PublishError("Airport manifest does not describe the verified 60 fps native scene")
    runways = manifest.get("runways")
    if not isinstance(runways, dict) or set(runways) != {"north", "center", "south", "west"}:
        raise PublishError("Airport manifest is missing one or more of the four runway records")
    integration = manifest.get("integration", {})
    if "HourForecast.od" not in integration.get("od", ""):
        raise PublishError("Airport manifest OD mapping no longer names HourForecast.od")
    if "HourForecast.p_18_usable" not in integration.get("runway18", ""):
        raise PublishError("Airport manifest runway-18 mapping no longer names its forecast probability")
    return raw


def verify_sources() -> dict[str, tuple[Path, int, str]]:
    verification = load_json(VERIFICATION_FILE)
    if verification.get("result") != "passed":
        raise PublishError("Native Blender verification is not marked passed")

    records: dict[str, dict[str, Any]] = {}
    for record in verification.get("assets", []):
        if isinstance(record, dict) and isinstance(record.get("file"), str):
            if record["file"] in records:
                raise PublishError(f"Duplicate asset record in verification.json: {record['file']}")
            records[record["file"]] = record

    verified: dict[str, tuple[Path, int, str]] = {}
    for name in GLB_ASSETS:
        record = records.get(name)
        if not record:
            raise PublishError(f"No verified hash for {name} in verification.json")
        path = EXPORT_ROOT / name
        if not path.is_file():
            raise PublishError(f"Missing Blender export: {path}")
        size = path.stat().st_size
        digest = sha256(path)
        if size != record.get("bytes") or digest != record.get("sha256"):
            raise PublishError(f"Export does not match verification.json: {name}")
        verified[name] = (path, size, digest)

    manifest_bytes = verify_manifest()
    verified["manifest.json"] = (
        MANIFEST_FILE,
        len(manifest_bytes),
        hashlib.sha256(manifest_bytes).hexdigest(),
    )
    return verified


def check_published(verified: dict[str, tuple[Path, int, str]]) -> None:
    for name, (source, size, digest) in verified.items():
        destination = WEB_ROOT / name
        if not destination.is_file():
            raise PublishError(f"Published web asset is missing: {destination}")
        if destination.stat().st_size != size or sha256(destination) != digest:
            raise PublishError(f"Published web asset is stale or changed: {destination}")
        print(f"OK  {name}  sha256={digest}")


def publish(verified: dict[str, tuple[Path, int, str]]) -> None:
    WEB_ROOT.mkdir(parents=True, exist_ok=True)
    staged: dict[str, Path] = {}
    try:
        # Stage the complete set before replacing any published asset.
        for name, (source, _size, expected_hash) in verified.items():
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=f".{name}.", suffix=".tmp", dir=WEB_ROOT, delete=False
            ) as temporary:
                staged_path = Path(temporary.name)
                with source.open("rb") as source_file:
                    shutil.copyfileobj(source_file, temporary, length=1024 * 1024)
                temporary.flush()
                os.fsync(temporary.fileno())
            if sha256(staged_path) != expected_hash:
                raise PublishError(f"Staged copy changed while publishing: {name}")
            staged[name] = staged_path

        for name in PUBLISHED_FILES:
            os.replace(staged[name], WEB_ROOT / name)
        check_published(verified)
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="verify sources and show intended copies")
    mode.add_argument("--check", action="store_true", help="verify sources and compare published copies without writing")
    args = parser.parse_args()

    try:
        verified = verify_sources()
        if args.check:
            check_published(verified)
            return 0
        if args.dry_run:
            for name, (_path, size, digest) in verified.items():
                print(f"WOULD PUBLISH  {name}  {size} bytes  sha256={digest}")
            return 0
        publish(verified)
        print(f"Published and verified {len(verified)} files in {WEB_ROOT}")
        return 0
    except (OSError, PublishError) as error:
        print(f"airport publish failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
