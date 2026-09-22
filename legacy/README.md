# Legacy reconstruction archive

This directory preserves obsolete reconstruction assets for technical history and auditability.

These files are **not part of the active Build 45 installer path** and must not be packaged into the current patcher.

## Contents

- `build15/`: historical retail Steam -> Build 15 reconstruction chain.
- `build44/`: historical Build 15 -> validated Steam Build 44 reconstruction chain.
- `gog-cjpg1/`: retired GOG CJPG1 experiment. This artifact was found malformed/truncated during Build 45 installer validation and must never be used for current releases.
- `gog-direct-probe/`: intermediate standalone GOG direct-delta artifact superseded by the embedded COJDP1 payloads in the current installer.

The active installer uses edition-specific embedded COJDP1 direct deltas and verifies both source and target SHA-256 values.
