#!/usr/bin/env python3
"""Upgrade an exact reconstructed Build 15 to validated Build 44.

Run patcher.py first to reconstruct Build 15 from the unmodified Steam files,
then run this script against that Build 15 directory.
"""
from __future__ import annotations
import argparse, base64, binascii, hashlib, io, json, struct, zlib
from pathlib import Path
from zipfile import ZipFile

CJPD_MAGIC = b"CJPD1"
PASSWORD = b"TN2kTjNmBvn5axaS6tGY"
LOCAL_SIG = 0x04034B50
CENTRAL_SIG = 0x02014B50
EOCD_SIG = 0x06054B50

BUILD15_EXE = "b468197ddcba6547db8dda2efc3cd29f524f57992756aa813142b5531b2fd78d"
BUILD15_DATA0 = "ffa18821657e8f25063897a28730a03fb962abf22d572fb3d4fdd83772db0eab"
BUILD44_EXE = "125a3b088e502049913d7a6d20f0ad76d7a0e5fe086d14bb257c4d0798ca5844"
BUILD44_DATA0 = "55cab794160a244ef3db3abfa0e3beb23643ebb20c3d95831d0c553905372744"

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def apply_cjpd1(source: bytes, patch_bytes: bytes) -> bytes:
    raw = zlib.decompress(patch_bytes)
    if raw[:5] != CJPD_MAGIC:
        raise ValueError("Invalid CJPD1 patch")
    pos = 5
    _block, source_size, target_size = struct.unpack_from("<IQQ", raw, pos); pos += 20
    source_hash = raw[pos:pos+32]; pos += 32
    target_hash = raw[pos:pos+32]; pos += 32
    op_count, = struct.unpack_from("<I", raw, pos); pos += 4
    if len(source) != source_size or hashlib.sha256(source).digest() != source_hash:
        raise ValueError("EXE is not the exact Build 15 source")
    out = bytearray()
    for _ in range(op_count):
        op = raw[pos:pos+1]; pos += 1
        if op == b"C":
            off, ln = struct.unpack_from("<QI", raw, pos); pos += 12
            out += source[off:off+ln]
        elif op == b"D":
            ln, = struct.unpack_from("<I", raw, pos); pos += 4
            out += raw[pos:pos+ln]; pos += ln
        else:
            raise ValueError("Unknown CJPD1 opcode")
    result = bytes(out)
    if len(result) != target_size or hashlib.sha256(result).digest() != target_hash:
        raise ValueError("EXE output verification failed")
    return result

_CRC_TABLE = []
for n in range(256):
    c = n
    for _ in range(8):
        c = (0xEDB88320 ^ (c >> 1)) if (c & 1) else (c >> 1)
    _CRC_TABLE.append(c)

def _crc_update(crc: int, byte: int) -> int:
    return ((crc >> 8) ^ _CRC_TABLE[(crc ^ byte) & 0xFF]) & 0xFFFFFFFF

def zipcrypto(data: bytes, decrypt: bool = False) -> bytes:
    key0, key1, key2 = 0x12345678, 0x23456789, 0x34567890
    def update(b: int):
        nonlocal key0, key1, key2
        key0 = _crc_update(key0, b)
        key1 = (key1 + (key0 & 0xFF)) & 0xFFFFFFFF
        key1 = (key1 * 134775813 + 1) & 0xFFFFFFFF
        key2 = _crc_update(key2, (key1 >> 24) & 0xFF)
    for b in PASSWORD:
        update(b)
    out = bytearray()
    for value in data:
        temp = (key2 | 2) & 0xFFFFFFFF
        mask = ((temp * (temp ^ 1)) >> 8) & 0xFF
        if decrypt:
            plain = value ^ mask
            out.append(plain); update(plain)
        else:
            out.append(value ^ mask); update(value)
    return bytes(out)

def apply_recipe(original: bytes, recipe: dict) -> bytes:
    lines = original.splitlines(keepends=True)
    out = []
    for op in recipe["ops"]:
        if op[0] == "copy":
            out.extend(lines[op[1]:op[2]])
        elif op[0] == "text":
            out.append(op[1].encode("utf-8"))
        else:
            raise ValueError("Unknown recipe opcode")
    return b"".join(out)

def local_record(data: bytes, archive: ZipFile, infos, index: int):
    start = infos[index].header_offset
    end = infos[index+1].header_offset if index+1 < len(infos) else archive.start_dir
    record = data[start:end]
    vals = struct.unpack("<IHHHHHIIIHH", record[:30])
    sig, ver, flag, method, mt, md, crc, cs, us, nl, xl = vals
    if sig != LOCAL_SIG:
        raise ValueError("Invalid local ZIP record")
    return record, {
        "ver":ver, "flag":flag, "method":method, "mt":mt, "md":md,
        "crc":crc, "cs":cs, "us":us, "name":record[30:30+nl],
        "extra":record[30+nl:30+nl+xl], "payload_offset":30+nl+xl,
        "tail":record[30+nl+xl+infos[index].compress_size:]
    }

def central_records(data: bytes, archive: ZipFile):
    records = []
    pos = archive.start_dir
    for _ in archive.infolist():
        vals = struct.unpack("<IHHHHHHIIIHHHHHII", data[pos:pos+46])
        if vals[0] != CENTRAL_SIG:
            raise ValueError("Invalid central ZIP record")
        nl, xl, cl = vals[10], vals[11], vals[12]
        ln = 46 + nl + xl + cl
        records.append(bytearray(data[pos:pos+ln]))
        pos += ln
    return records

def rebuild_data0(source: bytes, overlay: dict) -> bytes:
    name = overlay["entry"]; recipe = overlay["recipe"]; meta = overlay["metadata"]
    with ZipFile(io.BytesIO(source)) as archive:
        infos = archive.infolist()
        if len(infos) != 1774:
            raise ValueError("Unexpected Data0 entry count")
        centrals = central_records(source, archive)
        output = bytearray(); offsets = []; changed_index = None
        for i, info in enumerate(infos):
            offsets.append(len(output))
            record, loc = local_record(source, archive, infos, i)
            if info.filename != name:
                output += record
                continue
            changed_index = i
            payload = record[loc["payload_offset"]:loc["payload_offset"]+info.compress_size]
            plain = zlib.decompress(zipcrypto(payload, decrypt=True)[12:], -15)
            target = apply_recipe(plain, recipe)
            lm = meta["local"]
            compressor = zlib.compressobj(meta["level"], zlib.DEFLATED, -15, 8, zlib.Z_DEFAULT_STRATEGY)
            compressed = compressor.compress(target) + compressor.flush()
            crc = binascii.crc32(target) & 0xFFFFFFFF
            encrypted = zipcrypto(bytes.fromhex(meta["enc_header_hex"]) + compressed)
            if crc != lm["crc"] or len(encrypted) != lm["cs"] or len(target) != lm["us"]:
                raise ValueError("Build 44 HUD reconstruction mismatch")
            nb = name.encode("ascii"); extra = bytes.fromhex(lm["extra"])
            output += struct.pack("<IHHHHHIIIHH", LOCAL_SIG, lm["ver"], lm["flag"], lm["method"],
                                  lm["mt"], lm["md"], lm["crc"], lm["cs"], lm["us"], len(nb), len(extra))
            output += nb + extra + encrypted + bytes.fromhex(lm["tail"])
        if changed_index is None:
            raise ValueError("HUD entry not found")
        central_start = len(output)
        for i, info in enumerate(infos):
            if i != changed_index:
                raw = centrals[i]
                struct.pack_into("<I", raw, 42, offsets[i])
                output += raw
                continue
            cm = meta["central"]; nb = name.encode("ascii")
            extra = bytes.fromhex(cm["extra"]); comment = bytes.fromhex(cm["comment"])
            output += struct.pack("<IHHHHHHIIIHHHHHII", CENTRAL_SIG, cm["vm"], cm["vn"],
                                  cm["flag"], cm["method"], cm["mt"], cm["md"], cm["crc"],
                                  cm["cs"], cm["us"], len(nb), len(extra), len(comment),
                                  cm["disk"], cm["inta"], cm["exta"], offsets[i])
            output += nb + extra + comment
        central_size = len(output) - central_start
        count = len(infos)
        output += struct.pack("<IHHHHIIH", EOCD_SIG, 0, 0, count, count, central_size, central_start, 0)
        return bytes(output)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build15-dir", type=Path, default=Path("build15"))
    ap.add_argument("--output-dir", type=Path, default=Path("build44"))
    args = ap.parse_args()
    root = Path(__file__).resolve().parent
    exe15 = (args.build15_dir/"CoJGunslinger.exe").read_bytes()
    data15 = (args.build15_dir/"Data0.pak").read_bytes()
    if sha256(exe15) != BUILD15_EXE or sha256(data15) != BUILD15_DATA0:
        raise ValueError("Input directory is not exact reconstructed Build 15")
    patch = base64.b64decode((root/"patches/verified/CoJGunslinger.build44_from_build15.cjpd.b64").read_text(encoding="ascii"))
    exe44 = apply_cjpd1(exe15, patch)
    overlay = json.loads((root/"build44/data0_overlay.json").read_text(encoding="utf-8"))
    data44 = rebuild_data0(data15, overlay)
    if sha256(exe44) != BUILD44_EXE or sha256(data44) != BUILD44_DATA0:
        raise ValueError("Build 44 final hash verification failed")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/"CoJGunslinger.exe").write_bytes(exe44)
    (args.output_dir/"Data0.pak").write_bytes(data44)
    print("[OK] Build 44 reconstructed exactly")
    print("EXE  ", BUILD44_EXE)
    print("Data0", BUILD44_DATA0)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
