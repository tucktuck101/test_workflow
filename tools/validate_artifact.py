"""Validate a model artifact against a manifest and allowlist.

Usage:
  python -m tools.validate_artifact --artifact path --manifest manifest.json --root allowed/root --device cpu

Returns exit code 0 on success; non-zero on validation failure. Prints JSON result.
"""
import argparse
import json
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    import hashlib

    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_path(artifact: Path, root: Path | None) -> str | None:
    try:
        if root is not None:
            artifact.resolve().relative_to(root.resolve())
    except Exception:
        return "path_outside_root"
    if not artifact.exists():
        return "missing_model"
    if not artifact.is_file():
        return "path_invalid"
    return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate model artifact")
    parser.add_argument("--artifact", required=True, help="Path to model artifact")
    parser.add_argument("--manifest", required=True, help="Path to manifest.json")
    parser.add_argument("--root", help="Allowlisted root directory", default=None)
    parser.add_argument("--device", help="Expected device", default=None)
    args = parser.parse_args(argv)

    artifact_path = Path(args.artifact).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser().resolve()
    root = Path(args.root).expanduser().resolve() if args.root else None

    result: dict = {"artifact": str(artifact_path), "manifest": str(manifest_path)}

    path_error = validate_path(artifact_path, root)
    if path_error:
        result["status"] = "failed"
        result["reason"] = path_error
        print(json.dumps(result, indent=2))
        return 1

    if not manifest_path.exists():
        result["status"] = "failed"
        result["reason"] = "missing_manifest"
        print(json.dumps(result, indent=2))
        return 1

    try:
        manifest = json.loads(manifest_path.read_text())
    except Exception:
        result["status"] = "failed"
        result["reason"] = "invalid_manifest"
        print(json.dumps(result, indent=2))
        return 1

    expected_hash = str(manifest.get("hash", ""))
    expected_device = manifest.get("device")
    digest = sha256_file(artifact_path)
    result["computed_hash"] = digest
    result["expected_hash"] = expected_hash

    if digest.lower() != expected_hash.lower():
        result["status"] = "failed"
        result["reason"] = "hash_mismatch"
        print(json.dumps(result, indent=2))
        return 1

    if args.device and expected_device and args.device.lower() != str(expected_device).lower():
        result["status"] = "failed"
        result["reason"] = "device_mismatch"
        print(json.dumps(result, indent=2))
        return 1

    result["status"] = "ok"
    result["version"] = manifest.get("version")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
