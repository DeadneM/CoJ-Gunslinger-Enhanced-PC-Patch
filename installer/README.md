# Windows patcher

The active installer is the unified Steam + GOG patcher for the cumulative Enhanced PC Patch.

Current version designation:

`v2Pv45Sv45G`

- patcher: **v2P**
- Steam payload: **v45S**
- GOG payload: **v45G**

The installer version is independent from the game payload versions. A packaging-only change can therefore increment the patcher generation without implying that either gameplay payload changed.

## Detection

The patcher hashes `CoJGunslinger.exe` and `Data0.pak` before modification.

Accepted pairs:

- exact original Steam files;
- exact Steam Enhanced PC Patch Build 15 files;
- exact original GOG files;
- exact current Steam or GOG target, detected as already installed.

Mixed, unknown or previously modified pairs are refused.

## Reconstruction

The active installer embeds six compressed `COJDP1` direct deltas.

Supported source paths:

- Steam retail -> Steam v45
- Steam Build 15 -> Steam v45
- GOG retail -> GOG v45

EXE and Data0 are patched independently.

Each direct delta verifies its own expected source size/SHA-256 and target size/SHA-256. The installer also performs edition-level hash verification before staging and after final replacement.

The historical semantic Build 15 / Build 44 reconstruction chain and the retired GOG CJPG1 experiment are preserved under `legacy/` for audit/history only. They are not part of the active installer path.

## Edition preservation

The Steam path keeps Steam integration and the validated Steam payload.

The GOG path keeps the GOG entry point/platform integration and its four store-specific menu resources. It does not add Steam DRM or Steam-only navigation.

## Installation safety

The patcher creates `.Backup` copies only after recognizing a supported pair.

It then:

1. reconstructs the edition-specific target in a temporary directory;
2. verifies exact SHA-256 target hashes;
3. stages both files as temporary replacement files;
4. keeps a fresh rollback pair during replacement;
5. replaces the EXE and Data0;
6. verifies the installed target hashes again.

## Building

`.github/workflows/build-patcher.yml` builds development artifacts.

`.github/workflows/publish-release.yml` publishes the public executable.

Both workflows use Python 3.12 and PyInstaller.

The active patcher source already contains the compact direct-delta payloads. Legacy reconstruction assets therefore do not need to be packaged into the final executable. The workflow cleanup is intentionally handled as a separate repository-cleanup step.

The packaged executable contains no retail game EXE or retail `Data0.pak`.
