"""Command-line entry point for backup integrity checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from backup_integrity.manifest import create_manifest, verify_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create or verify backup SHA-256 manifests.")
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create", help="Create a checksum manifest")
    create.add_argument("directory", type=Path)
    create.add_argument("--output", type=Path, required=True)

    verify = commands.add_parser("verify", help="Verify files against a manifest")
    verify.add_argument("directory", type=Path)
    verify.add_argument("manifest", type=Path)
    verify.add_argument("--json", dest="json_path", type=Path)
    args = parser.parse_args(argv)

    try:
        if args.command == "create":
            result = create_manifest(args.directory)
            args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print(f"Manifest created: {args.output} ({len(result['files'])} files)")
            return 0

        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = verify_manifest(args.directory, manifest)
        rendered = json.dumps(result, indent=2)
        print(rendered)
        if args.json_path:
            args.json_path.write_text(rendered + "\n", encoding="utf-8")
        return 0 if result["verified"] else 1
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"backup-integrity: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
