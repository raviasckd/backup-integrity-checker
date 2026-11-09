# Backup Integrity Checker

A dependency-free Python CLI that records and verifies SHA-256 checksums for backup files.

## Features

- Builds a JSON manifest of regular files in a backup directory.
- Verifies files against a previously generated manifest.
- Reports missing, changed, and unexpected files.
- Rejects manifest paths that resolve outside the selected backup root.
- Does not modify backup contents during verification.

## Requirements

- Python 3.10+
- No third-party runtime dependencies

## Usage

Create a manifest:

```bash
python -m backup_integrity create ./backup --output backup-manifest.json
```

Verify the backup later:

```bash
python -m backup_integrity verify ./backup backup-manifest.json
python -m backup_integrity verify ./backup backup-manifest.json --json verification.json
```

Keep the manifest separate from the backup being measured, and store a copy independently. A checksum manifest cannot prove that the original backup source was complete or trustworthy.

## Development

```bash
python -m unittest discover -s tests -v
```

## License

MIT. See [LICENSE](LICENSE).
