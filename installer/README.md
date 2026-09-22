# Windows patcher

`COJ_Gunslinger_Patcher.exe` is the standalone Windows installer for the cumulative Enhanced PC Patch. The current validated target is **Build 44**.

## Accepted inputs

- exact original Steam `CoJGunslinger.exe` + `Data0.pak`;
- exact Enhanced PC Patch Build 15 pair;
- exact Build 44 pair, detected as already installed.

Unknown or mixed files are refused before modification.

## Installation safety

The patcher hashes both files first, creates `.Backup` copies only for recognized inputs, reconstructs the target in a temporary directory, verifies the exact Build 44 SHA-256 values, stages the pair, performs transactional replacement, and verifies the installed files again.

Validated Build 44:

- EXE: `125a3b088e502049913d7a6d20f0ad76d7a0e5fe086d14bb257c4d0798ca5844`
- Data0: `55cab794160a244ef3db3abfa0e3beb23643ebb20c3d95831d0c553905372744`

## Building the executable

The repository workflow `.github/workflows/build-patcher.yml` builds the patcher on `windows-latest` with Python 3.12 and PyInstaller.

The generated executable is:

`COJ_Gunslinger_Patcher.exe`

The executable embeds only the reconstruction code, compact patch data and metadata contained in this repository. It does not embed the retail game EXE or retail `Data0.pak`.
