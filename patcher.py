#!/usr/bin/env python3
"""
Call of Juarez: Gunslinger Enhanced PC Patch - deterministic Build 15 patcher.

This program applies CJPD1 binary deltas to verified retail game files.
It does not contain or distribute the original game binaries.

Python 3.8+; standard library only.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

MAGIC = b"CJPD1"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def apply_cjpd1(source: bytes, patch_bytes: bytes) -> bytes:
    raw = zlib.decompress(patch_bytes)
    pos = 0
    if raw[:5] != MAGIC:
        raise ValueError("Invalid CJPD1 patch magic")
    pos = 5

    block_size, source_size, target_size = struct.unpack_from("<IQQ", raw, pos)
    pos += 20
    source_hash = raw[pos:pos+32]
    pos += 32
    target_hash = raw[pos:pos+32]
    pos += 32
    (op_count,) = struct.unpack_from("<I", raw, pos)
    pos += 4

    if len(source) != source_size:
        raise ValueError(f"Wrong source size: {len(source)} != {source_size}")
    if hashlib.sha256(source).digest() != source_hash:
        raise ValueError("Wrong source SHA-256: file is not the expected retail original")

    output = bytearray()
    for _ in range(op_count):
        op = raw[pos:pos+1]
        pos += 1
        if op == b"C":
            source_offset, length = struct.unpack_from("<QI", raw, pos)
            pos += 12
            end = source_offset + length
            if end > len(source):
                raise ValueError("Patch COPY operation exceeds source file")
            output.extend(source[source_offset:end])
        elif op == b"D":
            (length,) = struct.unpack_from("<I", raw, pos)
            pos += 4
            end = pos + length
            if end > len(raw):
                raise ValueError("Patch DATA operation exceeds patch payload")
            output.extend(raw[pos:end])
            pos = end
        else:
            raise ValueError(f"Unknown CJPD1 opcode: {op!r}")

    result = bytes(output)
    if len(result) != target_size:
        raise ValueError(f"Wrong reconstructed size: {len(result)} != {target_size}")
    if hashlib.sha256(result).digest() != target_hash:
        raise ValueError("Reconstructed SHA-256 does not match the expected target")
    return result

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reconstruct Call of Juarez: Gunslinger Enhanced PC Patch Build 15 from verified retail files."
    )
    parser.add_argument(
        "--game-dir",
        type=Path,
        default=Path("."),
        help="Game directory containing CoJGunslinger.exe and Data0.pak (default: current directory)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("build15"),
        help="Directory for reconstructed patched files (default: ./build15)",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite the verified retail files after successful reconstruction. Backups are NOT created.",
    )
    args = parser.parse_args()

    repo_dir = Path(__file__).resolve().parent
    manifest = json.loads((repo_dir / "HASHES.json").read_text(encoding="utf-8"))

    game_dir = args.game_dir.resolve()
    output_dir = game_dir if args.in_place else args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    for item in manifest["files"]:
        source_path = game_dir / item["input_name"]
        patch_entries = item.get("patch_parts") or [item["patch"]]
        patch_paths = [repo_dir / entry for entry in patch_entries]
        target_path = output_dir / item["input_name"]

        if not source_path.is_file():
            print(f"[ERROR] Missing source: {source_path}", file=sys.stderr)
            return 2

        actual_source_hash = sha256_file(source_path)
        if actual_source_hash != item["original_sha256"]:
            print(f"[ERROR] {item['input_name']}: unexpected retail SHA-256", file=sys.stderr)
            print(f"        expected {item['original_sha256']}", file=sys.stderr)
            print(f"        got      {actual_source_hash}", file=sys.stderr)
            return 3

        if item.get("patch_encoding") == "base85":
            encoded = "".join(
                "".join(path.read_text(encoding="ascii").split())
                for path in patch_paths
            )
            patch_bytes = base64.b85decode(encoded.encode("ascii"))
        else:
            patch_bytes = b"".join(path.read_bytes() for path in patch_paths)

        patch_hash = hashlib.sha256(patch_bytes).hexdigest()
        if patch_hash != item["patch_sha256"]:
            print(f"[ERROR] Patch payload failed SHA-256 verification: {', '.join(map(str, patch_paths))}", file=sys.stderr)
            return 4

        reconstructed = apply_cjpd1(source_path.read_bytes(), patch_bytes)

        # Write only after every built-in integrity check passes.
        target_path.write_bytes(reconstructed)
        output_hash = sha256_file(target_path)
        if output_hash != item["output_sha256"]:
            print(f"[ERROR] Post-write verification failed: {target_path}", file=sys.stderr)
            return 5

        print(f"[OK] {item['input_name']}")
        print(f"     retail : {actual_source_hash}")
        print(f"     build15: {output_hash}")
        print(f"     bytes  : {len(reconstructed)}")

    print("Build 15 reconstructed successfully. All outputs match the reference SHA-256 values.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
