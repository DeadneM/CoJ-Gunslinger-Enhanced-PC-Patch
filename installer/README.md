# Windows patcher

`COJ_Gunslinger_Patcher_Build45.exe` is the standalone installer for the cumulative Enhanced PC Patch. Build 45 uses one executable for the supported **Steam and GOG** editions.

## Detection

The patcher hashes `CoJGunslinger.exe` and `Data0.pak` before modification.

Accepted pairs:

- exact original Steam files;
- exact Steam Enhanced PC Patch Build 15 files;
- exact original GOG files;
- exact current Steam or GOG target, detected as already installed.

Mixed, unknown or previously modified pairs are refused.

## Edition preservation

The Steam path keeps Steam integration and the validated Steam payload.

The GOG path keeps the GOG entry point/platform integration and its four store-specific menu resources. It does not add Steam DRM or Steam-only navigation.

## Installation safety

The patcher creates `.Backup` copies only after recognizing a supported pair. It reconstructs the edition-specific target in a temporary directory, verifies exact SHA-256 values, stages both files, keeps a rollback pair during replacement, and verifies the installed files again.

## Building

`.github/workflows/build-patcher.yml` builds the latest development artifact.

`.github/workflows/publish-release.yml` builds the versioned public executable when `release/VERSION` changes.

Both workflows use Python 3.12 and PyInstaller. The packaged executable contains reconstruction code and compact patch metadata only. It contains no retail game EXE or retail `Data0.pak`.
