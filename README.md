# CoJ-Gunslinger-Enhanced-PC-Patch

Deterministic source patcher for the **Call of Juarez: Gunslinger Enhanced PC Patch**.

This repository does **not** redistribute the retail game executable or `Data0.pak`.

## Reproducibility status

The Build 15 reconstruction was verified locally against the supplied retail originals and reference Build 15 files:

- `CoJGunslinger.exe`: byte-for-byte identical
- `Data0.pak`: byte-for-byte identical

The EXE CJPD1 delta is present in the repository and is reproducible directly.

The validated Data0 CJPD1 delta is **166,733 bytes** with SHA-256:

`b34d7c851f66db22ec8361935f388f0db7bf840d43ccd3f6afcc5c83639f1148`

It is intentionally not committed yet because the current connector text/base64 transport altered or truncated binary data during upload tests. A corrupted payload is not accepted as source of truth.

Expected Data0 destination once uploaded without conversion:

`patches/verified/Data0.build15.cjpd`

See `HASHES.json` and `VERIFY_REPORT.txt` for exact retail and Build 15 hashes.
