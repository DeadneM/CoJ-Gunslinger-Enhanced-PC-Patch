#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import struct
import sys
import tempfile
import traceback
import zlib
from pathlib import Path

import patcher as b15
import patcher_build44 as b44

LATEST_BUILD = 45

STEAM_RETAIL_EXE = "ca1c4766900feb867372e0e2e87eb5adb92ca26ee537598a034ed7be1313d93c"
STEAM_RETAIL_DATA0 = "0debd38c1560830486d8f7bdecf3806324e4f6357f1353ea0058b47bdfe8aa3b"
STEAM_BUILD15_EXE = "b468197ddcba6547db8dda2efc3cd29f524f57992756aa813142b5531b2fd78d"
STEAM_BUILD15_DATA0 = "ffa18821657e8f25063897a28730a03fb962abf22d572fb3d4fdd83772db0eab"
STEAM_TARGET_EXE = "125a3b088e502049913d7a6d20f0ad76d7a0e5fe086d14bb257c4d0798ca5844"
STEAM_TARGET_DATA0 = "55cab794160a244ef3db3abfa0e3beb23643ebb20c3d95831d0c553905372744"

GOG_RETAIL_EXE = "c061b0cd177c04e9ae30bdd5b8693caff2c2474b8f48f8d9c7e2bcd05f817708"
GOG_RETAIL_DATA0 = "7c5b83bc26a703abe4a55d460b73d0248168d16e7b2998d0d6e8a45244a03e60"
GOG_TARGET_EXE = "c0cc2bcb760e5b6fff9e6f0ab5e4ccf3acec5859f08f11a77339f551501a45e4"
GOG_TARGET_DATA0 = "601fdb9311635352af663b7c10959b263f5650a463f4dc20f1b54b390273d62b"


def bundle_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd().resolve()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_game_files(root: Path) -> tuple[Path, Path]:
    exe = root / "CoJGunslinger.exe"
    candidates = [root / "coj4" / "Data0.pak", root / "Data0.pak"]
    data0 = next((p for p in candidates if p.is_file()), candidates[0])
    if not exe.is_file():
        raise FileNotFoundError("CoJGunslinger.exe not found next to the patcher.")
    if not data0.is_file():
        raise FileNotFoundError("Data0.pak not found (expected coj4\\Data0.pak or Data0.pak).")
    return exe, data0


def backup_once(path: Path) -> Path:
    backup = path.with_name(path.name + ".Backup")
    if not backup.exists():
        shutil.copy2(path, backup)
    return backup


def build_steam_from_retail(exe: Path, data0: Path, temp: Path) -> tuple[Path, Path]:
    root = bundle_root()
    b15_dir = temp / "steam_build15"
    out_dir = temp / "steam_build45"
    b15_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((root / "HASHES.json").read_text(encoding="utf-8"))
    source_map = {"CoJGunslinger.exe": exe, "Data0.pak": data0}
    for item in manifest["files"]:
        source = source_map[item["input_name"]]
        if item["strategy"] == "cjpd1":
            result = b15.apply_cjpd1(source.read_bytes(), (root / item["patch"]).read_bytes())
        elif item["strategy"] == "semantic_data0":
            result = b15.rebuild_data0(source, root / item["source_dir"])
        else:
            raise ValueError("Unknown Build 15 reconstruction strategy")
        if len(result) != item["output_size"] or b15.sha256_bytes(result) != item["output_sha256"]:
            raise ValueError(f"Build 15 verification failed for {item['input_name']}")
        (b15_dir / item["input_name"]).write_bytes(result)

    return build_steam_from_build15(
        b15_dir / "CoJGunslinger.exe", b15_dir / "Data0.pak", temp, out_dir
    )


def build_steam_from_build15(
    exe: Path, data0: Path, temp: Path, out_dir: Path | None = None
) -> tuple[Path, Path]:
    root = bundle_root()
    out_dir = out_dir or (temp / "steam_build45")
    out_dir.mkdir(parents=True, exist_ok=True)

    patch44 = base64.b64decode(
        (root / "patches/verified/CoJGunslinger.build44_from_build15.cjpd.b64").read_text(
            encoding="ascii"
        )
    )
    exe_target = b44.apply_cjpd1(exe.read_bytes(), patch44)
    overlay = json.loads((root / "build44/data0_overlay.json").read_text(encoding="utf-8"))
    data_target = b44.rebuild_data0(data0.read_bytes(), overlay)

    out_exe = out_dir / "CoJGunslinger.exe"
    out_data = out_dir / "Data0.pak"
    out_exe.write_bytes(exe_target)
    out_data.write_bytes(data_target)
    return out_exe, out_data


def apply_gog_exe_patch(source: bytes, patch_b64: str) -> bytes:
    raw = zlib.decompress(base64.b64decode(patch_b64))
    if raw[:5] != b"CJPG1":
        raise ValueError("Invalid GOG EXE patch format")
    pos = 5
    source_size, target_size, count = struct.unpack_from("<III", raw, pos)
    pos += 12
    if len(source) != source_size:
        raise ValueError("Unexpected original GOG EXE size")

    out = bytearray(source)
    for _ in range(count):
        offset, length = struct.unpack_from("<II", raw, pos)
        pos += 8
        out[offset:offset + length] = raw[pos:pos + length]
        pos += length

    tail_length = struct.unpack_from("<I", raw, pos)[0]
    pos += 4
    out.extend(raw[pos:pos + tail_length])
    pos += tail_length
    if pos != len(raw):
        raise ValueError("Unexpected trailing GOG EXE patch data")
    del out[target_size:]
    return bytes(out)


def build_gog_from_retail(exe: Path, data0: Path, temp: Path) -> tuple[Path, Path]:
    root = bundle_root()
    out_dir = temp / "gog_build45"
    out_dir.mkdir(parents=True, exist_ok=True)

    patch_b64 = (
        root / "gog/build44/CoJGunslinger.gog44.cjpgz.b64"
    ).read_text(encoding="ascii")
    exe_target = apply_gog_exe_patch(exe.read_bytes(), patch_b64)

    # The 19 patch-modified source records are byte-identical between the
    # original Steam and GOG archives. The verified semantic recipe therefore
    # preserves GOG's four store-specific menu resources while rebuilding the
    # common modified resources deterministically.
    data15_hybrid = b15.rebuild_data0(data0, root / "data0")
    overlay = json.loads((root / "build44/data0_overlay.json").read_text(encoding="utf-8"))
    data_target = b44.rebuild_data0(data15_hybrid, overlay)

    out_exe = out_dir / "CoJGunslinger.exe"
    out_data = out_dir / "Data0.pak"
    out_exe.write_bytes(exe_target)
    out_data.write_bytes(data_target)
    return out_exe, out_data


def verify_target(edition: str, exe: Path, data0: Path) -> None:
    eh = sha256_file(exe)
    dh = sha256_file(data0)
    expected = {
        "Steam": (STEAM_TARGET_EXE, STEAM_TARGET_DATA0),
        "GOG": (GOG_TARGET_EXE, GOG_TARGET_DATA0),
    }[edition]
    if (eh, dh) != expected:
        raise ValueError(
            f"Final {edition} Build {LATEST_BUILD} verification failed.\n"
            f"EXE:   {eh}\nData0: {dh}"
        )


def pause() -> None:
    if getattr(sys, "frozen", False):
        try:
            input("\nPress Enter to close...")
        except EOFError:
            pass


def main() -> int:
    print("=" * 68)
    print(" Call of Juarez: Gunslinger - Enhanced PC Patch")
    print(f" Latest cumulative build: {LATEST_BUILD} | Steam + GOG")
    print("=" * 68)

    try:
        root = app_dir()
        exe, data0 = find_game_files(root)
        print(f"[OK] Game directory: {root}")
        print("[ .. ] Detecting edition and verifying game files...")
        eh = sha256_file(exe)
        dh = sha256_file(data0)

        if (eh, dh) == (STEAM_TARGET_EXE, STEAM_TARGET_DATA0):
            print(f"[OK] Steam Build {LATEST_BUILD} is already installed. Nothing to do.")
            return 0
        if (eh, dh) == (GOG_TARGET_EXE, GOG_TARGET_DATA0):
            print(f"[OK] GOG Build {LATEST_BUILD} is already installed. Nothing to do.")
            return 0

        if (eh, dh) == (STEAM_RETAIL_EXE, STEAM_RETAIL_DATA0):
            edition, source_kind = "Steam", "steam_retail"
            print("[OK] Original Steam files detected.")
        elif (eh, dh) == (STEAM_BUILD15_EXE, STEAM_BUILD15_DATA0):
            edition, source_kind = "Steam", "steam_build15"
            print("[OK] Steam Enhanced PC Patch Build 15 detected.")
        elif (eh, dh) == (GOG_RETAIL_EXE, GOG_RETAIL_DATA0):
            edition, source_kind = "GOG", "gog_retail"
            print("[OK] Original GOG files detected.")
        else:
            print("[ERROR] Unsupported or mixed game files.")
            print("        No files have been modified.")
            print(f"        EXE SHA-256:   {eh}")
            print(f"        Data0 SHA-256: {dh}")
            return 2

        eb = backup_once(exe)
        db = backup_once(data0)
        print(f"[OK] Edition: {edition}")
        print(f"[OK] Backup: {eb.name}")
        print(f"[OK] Backup: {db.name}")

        with tempfile.TemporaryDirectory(prefix="coj_patch_", dir=str(root)) as td:
            temp = Path(td)
            print(f"[ .. ] Building cumulative {edition} Build {LATEST_BUILD}...")
            if source_kind == "steam_retail":
                new_exe, new_data = build_steam_from_retail(exe, data0, temp)
            elif source_kind == "steam_build15":
                new_exe, new_data = build_steam_from_build15(exe, data0, temp)
            else:
                new_exe, new_data = build_gog_from_retail(exe, data0, temp)

            print("[ .. ] Verifying patched files before installation...")
            verify_target(edition, new_exe, new_data)
            print(f"[OK] {edition} Build {LATEST_BUILD} hashes verified.")

            staged_exe = exe.with_name(exe.name + ".PatchNew")
            staged_data = data0.with_name(data0.name + ".PatchNew")
            shutil.copy2(new_exe, staged_exe)
            shutil.copy2(new_data, staged_data)
            verify_target(edition, staged_exe, staged_data)

            rollback_exe = temp / "rollback_CoJGunslinger.exe"
            rollback_data = temp / "rollback_Data0.pak"
            shutil.copy2(exe, rollback_exe)
            shutil.copy2(data0, rollback_data)
            try:
                os.replace(staged_exe, exe)
                os.replace(staged_data, data0)
            except Exception:
                shutil.copy2(rollback_exe, exe)
                shutil.copy2(rollback_data, data0)
                raise

        verify_target(edition, exe, data0)
        print("=" * 68)
        print(f"[SUCCESS] {edition} Enhanced PC Patch Build {LATEST_BUILD} installed.")
        print("          Final SHA-256 verification passed.")
        print("=" * 68)
        return 0

    except Exception as exc:
        print("\n[ERROR]", exc)
        print("No unverified patched output was intentionally installed.")
        if os.environ.get("COJ_PATCHER_DEBUG") == "1":
            traceback.print_exc()
        return 1
    finally:
        pause()


if __name__ == "__main__":
    raise SystemExit(main())
