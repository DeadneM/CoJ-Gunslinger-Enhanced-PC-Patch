#!/usr/bin/env python3
"""Generate the PyInstaller Windows version resource from release/VERSION."""
from pathlib import Path

version = int(Path("release/VERSION").read_text(encoding="ascii").strip())
v = (version, 0, 0, 0)

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
          StringStruct('FileVersion', 'Build {version}'),
          StringStruct('InternalName', 'COJ_Gunslinger_Patcher'),
          StringStruct('OriginalFilename', 'COJ_Gunslinger_Patcher.exe'),
          StringStruct('ProductName', 'COJ Gunslinger Enhanced PC Patch'),
          StringStruct('ProductVersion', 'Build {version}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
Path("installer/version_info.txt").write_text(content, encoding="utf-8")
print(f"Generated Windows version resource for Build {version}")
