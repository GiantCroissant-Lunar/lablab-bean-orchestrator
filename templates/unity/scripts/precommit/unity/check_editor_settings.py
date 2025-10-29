#!/usr/bin/env python3
import os
import sys

path = os.path.join('ProjectSettings', 'EditorSettings.asset')
if not os.path.exists(path):
    print(f'Warning: {path} not found; skipping EditorSettings checks')
    sys.exit(0)

serialization_ok = False
visible_meta_ok = False

with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
    # Force Text == 2
    if 'm_SerializationMode: 2' in content:
        serialization_ok = True
    # Visible Meta Files keyword
    if 'Visible Meta Files' in content or 'm_ExternalVersionControlSupport: Visible Meta Files' in content:
        visible_meta_ok = True

errs = []
if not serialization_ok:
    errs.append('EditorSettings: m_SerializationMode should be 2 (Force Text).')
if not visible_meta_ok:
    errs.append('EditorSettings: Version control should be "Visible Meta Files".')

if errs:
    print('\n'.join(errs))
    print('\nOpen Unity: Edit > Project Settings > Editor\n- Asset Serialization: Force Text\n- Version Control: Visible Meta Files')
    sys.exit(1)

print('EditorSettings serialization + visible meta OK')

