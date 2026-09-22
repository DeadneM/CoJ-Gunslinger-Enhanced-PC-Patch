#!/usr/bin/env python3
"""Generate the PyInstaller Windows version resource from release/VERSION."""
import re
from pathlib import Path

designation = Path("release/VERSION").read_text(encoding="ascii").strip()
match = re.fullmatch(r"v(\d+)Pv(\d+)Sv(\d+)G", designation)
if not match:
    raise SystemExit(
        "release/VERSION must use the form v<PATCHER>Pv<STEAM>Sv<GOG>G "
        "(example: v2Pv45Sv45G)"
    )

patcher_version, steam_version, gog_version = map(int, match.groups())
v = (patcher_version, steam_version, gog_version, 0)
exe_name = f"COJ_Gunslinger_Patcher_{designation}.exe"

content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={v},
    prodvers={v},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', 'DeadneM'),
          StringStruct('FileDescription', 'Call of Juarez: Gunslinger Enhanced PC Patch'),
          StringStruct('FileVersion', '{designation}'),
          StringStruct('InternalName', 'COJ_Gunslinger_Patcher'),
          StringStruct('OriginalFilename', '{exe_name}'),
          StringStruct('ProductName', 'COJ Gunslinger Enhanced PC Patch'),
          StringStruct('ProductVersion', '{designation}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
Path("installer/version_info.txt").write_text(content, encoding="utf-8")
print(
    f"Generated Windows version resource for {designation} "
    f"(Patcher {patcher_version}, Steam {steam_version}, GOG {gog_version})"
)
