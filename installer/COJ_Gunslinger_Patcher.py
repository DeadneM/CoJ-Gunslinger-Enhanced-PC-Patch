#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

import patcher as b15
import patcher_build44 as b44

LATEST_BUILD = 44
RETAIL_EXE = "ca1c4766900feb867372e0e2e87eb5adb92ca26ee537598a034ed7be1313d93c"
RETAIL_DATA0 = "0debd38c1560830486d8f7bdecf3806324e4f6357f1353ea0058b47bdfe8aa3b"
BUILD15_EXE = "b468197ddcba6547db8dda2efc3cd29f524f57992756aa813142b5531b2fd78d"
BUILD15_DATA0 = "ffa18821657e8f25063897a28730a03fb962abf22d572fb3d4fdd83772db0eab"
BUILD44_EXE = "125a3b088e502049913d7a6d20f0ad76d7a0e5fe086d14bb257c4d0798ca5844"
BUILD44_DATA0 = "55cab794160a244ef3db3abfa0e3beb23643ebb20c3d95831d0c553905372744"


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


def build_from_retail(exe: Path, data0: Path, temp: Path) -> tuple[Path, Path]:
    root = bundle_root()
    b15_dir = temp / "build15"
    b44_dir = temp / "build44"
    b15_dir.mkdir(parents=True, exist_ok=True)
    b44_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((root / "HASHES.json").read_text(encoding="utf-8"))
    source_map = {"CoJGunslinger.exe": exe, "Data0.pak": data0}

    for item in manifest["files"]:
        source = source_map[item["input_name"]]
        if item["strategy"] == "cjpd1":
            patch_path = root / item["patch"]
            result = b15.apply_cjpd1(source.read_bytes(), patch_path.read_bytes())
        elif item["strategy"] == "semantic_data0":
            result = b15.rebuild_data0(source, root / item["source_dir"])
        else:
            raise ValueError("Unknown Build 15 reconstruction strategy")

        if len(result) != item["output_size"] or b15.sha256_bytes(result) != item["output_sha256"]:
            raise ValueError(f"Build 15 verification failed for {item['input_name']}")
        (b15_dir / item["input_name"]).write_bytes(result)

    exe15 = (b15_dir / "CoJGunslinger.exe").read_bytes()
    data15 = (b15_dir / "Data0.pak").read_bytes()

    patch44 = base64.b64decode(
        (root / "patches/verified/CoJGunslinger.build44_from_build15.cjpd.b64").read_text(encoding="ascii")
    )
    exe44 = b44.apply_cjpd1(exe15, patch44)
    overlay = json.loads((root / "build44/data0_overlay.json").read_text(encoding="utf-8"))
    data44 = b44.rebuild_data0(data15, overlay)

    out_exe = b44_dir / "CoJGunslinger.exe"
    out_data = b44_dir / "Data0.pak"
    out_exe.write_bytes(exe44)
    out_data.write_bytes(data44)
    return out_exe, out_data


def build_from_build15(exe: Path, data0: Path, temp: Path) -> tuple[Path, Path]:
    root = bundle_root()
    out_dir = temp / "build44"
    out_dir.mkdir(parents=True, exist_ok=True)

    patch44 = base64.b64decode(
        (root / "patches/verified/CoJGunslinger.build44_from_build15.cjpd.b64").read_text(encoding="ascii")
    )
    exe44 = b44.apply_cjpd1(exe.read_bytes(), patch44)
    overlay = json.loads((root / "build44/data0_overlay.json").read_text(encoding="utf-8"))
    data44 = b44.rebuild_data0(data0.read_bytes(), overlay)

    out_exe = out_dir / "CoJGunslinger.exe"
    out_data = out_dir / "Data0.pak"
    out_exe.write_bytes(exe44)
    out_data.write_bytes(data44)
    return out_exe, out_data


def verify_build44(exe: Path, data0: Path) -> None:
    eh = sha256_file(exe)
    dh = sha256_file(data0)
    if eh != BUILD44_EXE or dh != BUILD44_DATA0:
        raise ValueError(
            "Final Build 44 verification failed.\n"
            f"EXE:   {eh}\nData0: {dh}"
        )


def pause() -> None:
    if getattr(sys, "frozen", False):
        try:
            input("\nPress Enter to close...")
        except EOFError:
            pass


def main() -> int:
    print("=" * 64)
    print(" Call of Juarez: Gunslinger - Enhanced PC Patch")
    print(f" Latest cumulative build: {LATEST_BUILD}")
    print("=" * 64)

    try:
        root = app_dir()
        exe, data0 = find_game_files(root)
        print(f"[OK] Game directory: {root}")
        print("[ .. ] Verifying game files...")
        eh = sha256_file(exe)
        dh = sha256_file(data0)

        if eh == BUILD44_EXE and dh == BUILD44_DATA0:
            print(f"[OK] Build {LATEST_BUILD} is already installed. Nothing to do.")
            return 0

        if eh == RETAIL_EXE and dh == RETAIL_DATA0:
            source_kind = "retail"
            print("[OK] Original Steam files detected.")
        elif eh == BUILD15_EXE and dh == BUILD15_DATA0:
            source_kind = "build15"
            print("[OK] Enhanced PC Patch Build 15 detected.")
        else:
            print("[ERROR] Unsupported or mixed game files.")
            print("        No files have been modified.")
            print(f"        EXE SHA-256:   {eh}")
            print(f"        Data0 SHA-256: {dh}")
            return 2

        eb = backup_once(exe)
        db = backup_once(data0)
        print(f"[OK] Backup: {eb.name}")
        print(f"[OK] Backup: {db.name}")

        with tempfile.TemporaryDirectory(prefix="coj_patch_", dir=str(root)) as td:
            temp = Path(td)
            print(f"[ .. ] Building cumulative Build {LATEST_BUILD}...")
            if source_kind == "retail":
                new_exe, new_data = build_from_retail(exe, data0, temp)
            else:
                new_exe, new_data = build_from_build15(exe, data0, temp)

            print("[ .. ] Verifying patched files before installation...")
            verify_build44(new_exe, new_data)
            print("[OK] Build 44 hashes verified.")

            staged_exe = exe.with_name(exe.name + ".PatchNew")
            staged_data = data0.with_name(data0.name + ".PatchNew")
            shutil.copy2(new_exe, staged_exe)
            shutil.copy2(new_data, staged_data)
            verify_build44(staged_exe, staged_data)

            os.replace(staged_exe, exe)
            os.replace(staged_data, data0)

        verify_build44(exe, data0)
        print("=" * 64)
        print(f"[SUCCESS] Enhanced PC Patch Build {LATEST_BUILD} installed.")
        print("          Final SHA-256 verification passed.")
        print("=" * 64)
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
