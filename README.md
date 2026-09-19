# CoJ-Gunslinger-Enhanced-PC-Patch

Deterministic source patcher for the **Call of Juarez: Gunslinger Enhanced PC Patch**.

This repository does **not** redistribute the retail game executable or `Data0.pak`. Instead, it contains small Base85-encoded binary deltas and a standard-library Python patcher that reconstructs the validated **Build 15** from unmodified retail files.

## Required retail files

Place the repository next to these original files, using their normal game names:

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
2. patch SHA-256;
3. reconstructed output size and SHA-256.

For Build 15, the expected outputs are:

- `CoJGunslinger.exe`: `b468197ddcba6547db8dda2efc3cd29f524f57992756aa813142b5531b2fd78d`
- `Data0.pak`: `ffa18821657e8f25063897a28730a03fb962abf22d572fb3d4fdd83772db0eab`

The deltas are Base85 text wrappers around the simple documented `CJPD1` format implemented directly in `patcher.py`. Unchanged bytes are copied from the user's verified retail files; only modified data is stored in the patch payloads.
