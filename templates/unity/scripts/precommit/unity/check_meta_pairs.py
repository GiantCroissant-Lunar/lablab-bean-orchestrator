#!/usr/bin/env python3
import os
import sys

ROOT = os.getcwd()
ASSETS = os.path.join(ROOT, 'Assets')

missing_meta = []
orphan_meta = []

for base, dirs, files in os.walk(ASSETS):
    # Skip Library, Temp just in case
    dirs[:] = [d for d in dirs if d not in ('Library', 'Temp', 'Logs', 'Build')]
    names = set(files)
    for f in files:
        if f.endswith('.meta'):
            stem = f[:-5]
            if stem not in names:
                orphan_meta.append(os.path.relpath(os.path.join(base, f), ROOT))
        else:
            meta = f + '.meta'
            if meta not in names:
                missing_meta.append(os.path.relpath(os.path.join(base, f + '.meta'), ROOT))

err = 0
if missing_meta:
    print('Missing .meta files for:')
    for p in missing_meta:
        print('  ', p)
    err = 1
if orphan_meta:
    print('Orphan .meta files:')
    for p in orphan_meta:
        print('  ', p)
    err = 1

if err:
    print('\nFix: In Unity, reimport the folder or right-click -> Reimport to regenerate .meta files; delete or correct orphan metas.')
    sys.exit(1)

print('Unity meta pairing OK')
