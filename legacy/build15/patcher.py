#!/usr/bin/env python3
"""Deterministic Call of Juarez: Gunslinger Enhanced PC Patch Build 15 builder.

Requires only Python 3.8+ and unmodified retail game files.
The retail files themselves are not distributed by this repository.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path
from zipfile import ZipFile

CJPD_MAGIC = b"CJPD1"
DATA0_PASSWORD = b"TN2kTjNmBvn5axaS6tGY"
LOCAL_SIG = 0x04034B50
CENTRAL_SIG = 0x02014B50
EOCD_SIG = 0x06054B50


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def apply_cjpd1(source: bytes, patch_bytes: bytes) -> bytes:
    raw = zlib.decompress(patch_bytes)
    if raw[:5] != CJPD_MAGIC:
        raise ValueError("Invalid CJPD1 patch magic")
    pos = 5
    _block_size, source_size, target_size = struct.unpack_from("<IQQ", raw, pos)
    pos += 20
    source_hash = raw[pos:pos + 32]
    pos += 32
    target_hash = raw[pos:pos + 32]
    pos += 32
    (op_count,) = struct.unpack_from("<I", raw, pos)
    pos += 4

    if len(source) != source_size or hashlib.sha256(source).digest() != source_hash:
        raise ValueError("CJPD1 source does not match the expected retail file")

    out = bytearray()
    for _ in range(op_count):
        op = raw[pos:pos + 1]
        pos += 1
        if op == b"C":
            source_offset, length = struct.unpack_from("<QI", raw, pos)
            pos += 12
            out.extend(source[source_offset:source_offset + length])
        elif op == b"D":
            (length,) = struct.unpack_from("<I", raw, pos)
            pos += 4
            out.extend(raw[pos:pos + length])
            pos += length
        else:
            raise ValueError(f"Unknown CJPD1 opcode: {op!r}")

    result = bytes(out)
    if len(result) != target_size or hashlib.sha256(result).digest() != target_hash:
        raise ValueError("CJPD1 reconstructed output failed integrity verification")
    return result


# PKZIP classic ZipCrypto primitive.
_CRC_TABLE = []
for _n in range(256):
    _c = _n
    for _ in range(8):
        _c = (0xEDB88320 ^ (_c >> 1)) if (_c & 1) else (_c >> 1)
    _CRC_TABLE.append(_c)


def _crc_update(crc: int, byte: int) -> int:
    return ((crc >> 8) ^ _CRC_TABLE[(crc ^ byte) & 0xFF]) & 0xFFFFFFFF


def zipcrypto(data: bytes, password: bytes, decrypt: bool = False) -> bytes:
    key0, key1, key2 = 0x12345678, 0x23456789, 0x34567890

    def update(plain_byte: int) -> None:
        nonlocal key0, key1, key2
        key0 = _crc_update(key0, plain_byte)
        key1 = (key1 + (key0 & 0xFF)) & 0xFFFFFFFF
        key1 = (key1 * 134775813 + 1) & 0xFFFFFFFF
        key2 = _crc_update(key2, (key1 >> 24) & 0xFF)

    for b in password:
        update(b)

    out = bytearray()
    for value in data:
        temp = (key2 | 2) & 0xFFFFFFFF
        mask = ((temp * (temp ^ 1)) >> 8) & 0xFF
        if decrypt:
            plain = value ^ mask
            out.append(plain)
            update(plain)
        else:
            plain = value
            out.append(value ^ mask)
            update(plain)
    return bytes(out)


def _parse_local_record(path: Path, archive: ZipFile, infos, index: int):
    start = infos[index].header_offset
    end = infos[index + 1].header_offset if index + 1 < len(infos) else archive.start_dir
    with path.open("rb") as f:
        f.seek(start)
        record = f.read(end - start)
    fields = struct.unpack("<IHHHHHIIIHH", record[:30])
    sig, version, flag, method, mod_time, mod_date, crc, comp_size, uncomp_size, name_len, extra_len = fields
    if sig != LOCAL_SIG:
        raise ValueError(f"Invalid local ZIP record at offset {start}")
    name = record[30:30 + name_len]
    extra = record[30 + name_len:30 + name_len + extra_len]
    payload_offset = 30 + name_len + extra_len
    tail = record[payload_offset + infos[index].compress_size:]
    return record, {
        "version": version,
        "flag": flag,
        "method": method,
        "mod_time": mod_time,
        "mod_date": mod_date,
        "crc": crc,
        "comp_size": comp_size,
        "uncomp_size": uncomp_size,
        "name": name,
        "extra": extra,
        "payload_offset": payload_offset,
        "tail": tail,
    }


def _parse_central_records(path: Path, archive: ZipFile):
    records = []
    with path.open("rb") as f:
        f.seek(archive.start_dir)
        for _ in archive.infolist():
            fixed = f.read(46)
            values = struct.unpack("<IHHHHHHIIIHHHHHII", fixed)
            sig, vm, vn, flag, method, mt, md, crc, cs, us, nl, xl, cl, disk, inta, exta, offset = values
            if sig != CENTRAL_SIG:
                raise ValueError("Invalid central ZIP directory")
            name = f.read(nl)
            extra = f.read(xl)
            comment = f.read(cl)
            records.append(bytearray(fixed + name + extra + comment))
    return records


def _extract_plaintext(record: bytes, local: dict) -> bytes:
    payload = record[local["payload_offset"]:local["payload_offset"] + local["comp_size"]]
    decrypted = zipcrypto(payload, DATA0_PASSWORD, decrypt=True)
    if len(decrypted) < 12:
        raise ValueError("Encrypted Data0 entry is too short")
    return zlib.decompress(decrypted[12:], -15)


def _apply_recipe(original: bytes, recipe: dict) -> bytes:
    if recipe.get("base_transform") == "crlf_to_lf":
        original = original.replace(b"\r\n", b"\n")
    lines = original.splitlines(keepends=True)
    output = []
    for op in recipe["ops"]:
        if op[0] == "copy":
            output.extend(lines[op[1]:op[2]])
        elif op[0] == "text":
            output.append(op[1].encode("utf-8"))
        else:
            raise ValueError(f"Unknown Data0 recipe operation: {op[0]}")
    return b"".join(output)


def _load_json_groups(directory: Path, prefix: str) -> dict:
    merged = {}
    paths = sorted(directory.glob(f"{prefix}_*.json"))
    if not paths:
        raise FileNotFoundError(f"No {prefix} source files found in {directory}")
    for path in paths:
        part = json.loads(path.read_text(encoding="utf-8"))
        overlap = set(merged).intersection(part)
        if overlap:
            raise ValueError(f"Duplicate {prefix} entries: {sorted(overlap)}")
        merged.update(part)
    return merged


def rebuild_data0(original_path: Path, data0_dir: Path) -> bytes:
    recipes = _load_json_groups(data0_dir, "recipes")
    metadata = _load_json_groups(data0_dir, "metadata")
    changed = set(recipes)

    with ZipFile(original_path) as archive:
        infos = archive.infolist()
        if len(infos) != 1774:
            raise ValueError(f"Unexpected retail Data0 entry count: {len(infos)}")
        central_records = _parse_central_records(original_path, archive)

        output = bytearray()
        new_offsets = []

        for index, info in enumerate(infos):
            new_offsets.append(len(output))
            original_record, local = _parse_local_record(original_path, archive, infos, index)
            name = info.filename
            if name not in changed:
                output.extend(original_record)
                continue

            plain = _extract_plaintext(original_record, local)
            target_plain = _apply_recipe(plain, recipes[name])
            meta = metadata[name]
            lm = meta["local"]

            compressor = zlib.compressobj(
                meta["level"], zlib.DEFLATED, -15, 8, zlib.Z_DEFAULT_STRATEGY
            )
            compressed = compressor.compress(target_plain) + compressor.flush()
            crc = binascii.crc32(target_plain) & 0xFFFFFFFF
            encrypted = zipcrypto(bytes.fromhex(meta["enc_header_hex"]) + compressed, DATA0_PASSWORD)

            if crc != lm["crc"]:
                raise ValueError(f"CRC mismatch while rebuilding {name}")
            if len(encrypted) != lm["cs"] or len(target_plain) != lm["us"]:
                raise ValueError(f"Size mismatch while rebuilding {name}")

            name_bytes = name.encode("ascii")
            extra = bytes.fromhex(lm["extra"])
            record = struct.pack(
                "<IHHHHHIIIHH",
                LOCAL_SIG,
                lm["ver"], lm["flag"], lm["method"], lm["mt"], lm["md"],
                lm["crc"], lm["cs"], lm["us"], len(name_bytes), len(extra),
            )
            record += name_bytes + extra + encrypted + bytes.fromhex(lm["tail"])
            output.extend(record)

        central_start = len(output)
        for index, info in enumerate(infos):
            name = info.filename
            if name not in changed:
                raw = central_records[index]
                struct.pack_into("<I", raw, 42, new_offsets[index])
                output.extend(raw)
                continue

            cm = metadata[name]["central"]
            name_bytes = name.encode("ascii")
            extra = bytes.fromhex(cm["extra"])
            comment = bytes.fromhex(cm["comment"])
            output.extend(struct.pack(
                "<IHHHHHHIIIHHHHHII",
                CENTRAL_SIG,
                cm["vm"], cm["vn"], cm["flag"], cm["method"], cm["mt"], cm["md"],
                cm["crc"], cm["cs"], cm["us"],
                len(name_bytes), len(extra), len(comment),
                cm["disk"], cm["inta"], cm["exta"], new_offsets[index],
            ))
            output.extend(name_bytes + extra + comment)

        central_size = len(output) - central_start
        count = len(infos)
        output.extend(struct.pack(
            "<IHHHHIIH", EOCD_SIG, 0, 0, count, count, central_size, central_start, 0
        ))
        return bytes(output)


def build_one(repo_dir: Path, game_dir: Path, output_dir: Path, item: dict) -> None:
    source = game_dir / item["input_name"]
    if not source.is_file():
        raise FileNotFoundError(f"Missing source: {source}")
    if source.stat().st_size != item["original_size"] or sha256_file(source) != item["original_sha256"]:
        raise ValueError(f"{item['input_name']} is not the expected unmodified retail file")

    if item["strategy"] == "cjpd1":
        patch_path = repo_dir / item["patch"]
        patch = patch_path.read_bytes()
        if len(patch) != item["patch_size"] or sha256_bytes(patch) != item["patch_sha256"]:
            raise ValueError(f"EXE patch payload failed verification: {patch_path}")
        result = apply_cjpd1(source.read_bytes(), patch)
    elif item["strategy"] == "semantic_data0":
        result = rebuild_data0(source, repo_dir / item["source_dir"])
    else:
        raise ValueError(f"Unknown build strategy: {item['strategy']}")

    if len(result) != item["output_size"] or sha256_bytes(result) != item["output_sha256"]:
        raise ValueError(f"Rebuilt {item['input_name']} does not match Build 15")

    target = output_dir / item["input_name"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(result)
    print(f"[OK] {item['input_name']}")
    print(f"     SHA-256 {item['output_sha256']}")
    print(f"     bytes   {len(result)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconstruct Gunslinger Enhanced PC Patch Build 15 from retail files")
    parser.add_argument("--game-dir", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, default=Path("build15"))
    parser.add_argument("--in-place", action="store_true")
    args = parser.parse_args()

    repo_dir = Path(__file__).resolve().parent
    manifest = json.loads((repo_dir / "HASHES.json").read_text(encoding="utf-8"))
    game_dir = args.game_dir.resolve()
    output_dir = game_dir if args.in_place else args.output_dir.resolve()

    try:
        for item in manifest["files"]:
            build_one(repo_dir, game_dir, output_dir, item)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print("Build 15 reconstructed successfully. Both outputs match the validated reference hashes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
