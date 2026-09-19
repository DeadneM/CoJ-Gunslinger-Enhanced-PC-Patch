# CoJ-Gunslinger-Enhanced-PC-Patch

Deterministic source patcher for the **Call of Juarez: Gunslinger Enhanced PC Patch**.

This repository does **not** redistribute the retail game executable or `Data0.pak`. Instead, it contains Base85-encoded binary deltas and a standard-library Python patcher that reconstructs the validated **Build 15** from unmodified retail files.

## Required retail files

Point the patcher at a directory containing these original files under their normal game names:

- `CoJGunslinger.exe`
- `Data0.pak`

The patcher refuses to run unless both files match the exact retail SHA-256 values recorded in `HASHES.json`.

## Build

Python 3.8+ is sufficient. No external packages are required.

```bash
python patcher.py --game-dir "PATH_TO_GAME_FILES"
```

By default, reconstructed files are written to `./build15/`.

To replace verified originals directly:

```bash
python patcher.py --game-dir "PATH_TO_GAME_FILES" --in-place
```

## Reproducibility

The patcher verifies:

1. retail input size and SHA-256;
2. patch payload SHA-256;
3. reconstructed output size and SHA-256.

Expected Build 15 outputs:

- `CoJGunslinger.exe`: `b468197ddcba6547db8dda2efc3cd29f524f57992756aa813142b5531b2fd78d`
- `Data0.pak`: `ffa18821657e8f25063897a28730a03fb962abf22d572fb3d4fdd83772db0eab`

The Base85 payloads are split into small repository files only for transport. `patcher.py` concatenates the parts before decoding them. The decoded data is the same validated CJPD1 delta used for byte-for-byte reconstruction.

See `VERIFY_REPORT.txt` for the verification performed against the supplied Build 15 reference files.
