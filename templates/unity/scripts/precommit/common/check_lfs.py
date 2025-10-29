#!/usr/bin/env python3
import os
import subprocess
import sys

THRESHOLD_BYTES = int(os.environ.get('LFS_THRESHOLD_BYTES', str(5 * 1024 * 1024)))

def git_ls_files():
    out = subprocess.check_output(['git', 'ls-files', '-z'])
    return out.decode('utf-8', 'ignore').split('\x00')[:-1]

def file_size(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return 0

def has_lfs(path):
    try:
        out = subprocess.check_output(['git', 'check-attr', 'filter', '--', path])
        return b'lfs' in out
    except subprocess.CalledProcessError:
        return False

large_not_lfs = []
for f in git_ls_files():
    if not os.path.isfile(f):
        continue
    sz = file_size(f)
    if sz >= THRESHOLD_BYTES and not has_lfs(f):
        large_not_lfs.append((f, sz))

if large_not_lfs:
    print('Large files not tracked by LFS (threshold={} MB):'.format(THRESHOLD_BYTES // (1024*1024)))
    for f, sz in large_not_lfs:
        print('  {:>8.2f} MB  {}'.format(sz / (1024*1024), f))
    print('\nFix: git lfs track <pattern> and commit .gitattributes; then re-add files.')
    sys.exit(1)

print('LFS check OK')

