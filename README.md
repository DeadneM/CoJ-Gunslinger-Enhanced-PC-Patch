# CoJ-Gunslinger-Enhanced-PC-Patch

Deterministic source reconstruction for the **Call of Juarez: Gunslinger Enhanced PC Patch - Build 15**.

This repository does **not** redistribute the retail `CoJGunslinger.exe` or `Data0.pak`. It rebuilds the validated patched files from unmodified retail files and verifies the final SHA-256 hashes.

## Reproducibility status

Both Build 15 files are reproducible from the retail originals:

- `CoJGunslinger.exe` - deterministic CJPD1 binary delta
- `Data0.pak` - semantic reconstruction of the 19 modified resources, while copying all 1755 unchanged ZIP records byte-for-byte from the retail archive

The Data0 builder reproduces the archive layout, raw DEFLATE streams, PKZIP ZipCrypto encryption, local headers, data descriptors, central directory and offsets.

The resulting files were compared against the validated Build 15 references with full binary comparison (`cmp`), not hashes alone.

## Required retail files

Place the original Steam files in one directory under their normal names:

- `CoJGunslinger.exe`
- `Data0.pak`

Expected retail SHA-256 values:

- `CoJGunslinger.exe`: `ca1c4766900feb867372e0e2e87eb5adb92ca26ee537598a034ed7be1313d93c`
- `Data0.pak`: `0debd38c1560830486d8f7bdecf3806324e4f6357f1353ea0058b47bdfe8aa3b`

## Build

Python 3.8+ only. No third-party packages are required.

```bash
python patcher.py --game-dir "PATH_TO_RETAIL_FILES"
```

The rebuilt files are written to `./build15/` by default.

To patch the verified retail files in place:

```bash
python patcher.py --game-dir "PATH_TO_RETAIL_FILES" --in-place
```

## Expected Build 15 outputs

- `CoJGunslinger.exe`
  - size: `23203840`
  - SHA-256: `b468197ddcba6547db8dda2efc3cd29f524f57992756aa813142b5531b2fd78d`
- `Data0.pak`
  - size: `9350103`
  - SHA-256: `ffa18821657e8f25063897a28730a03fb962abf22d572fb3d4fdd83772db0eab`

## Source layout

- `patcher.py` - deterministic reconstruction tool
- `HASHES.json` - retail and Build 15 integrity manifest
- `patches/verified/CoJGunslinger.build15.cjpd` - compact EXE delta
- `data0/recipes_*.json` - readable plaintext transformation recipes for the 19 changed Data0 resources
- `data0/metadata_*.json` - ZIP/DEFLATE/ZipCrypto metadata needed to reproduce the exact Build 15 archive
- `VERIFY_REPORT.txt` - byte-for-byte verification record

The retail game files are intentionally excluded from this repository.
