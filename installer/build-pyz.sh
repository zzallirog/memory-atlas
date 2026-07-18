#!/usr/bin/env bash
# Thin wrapper — the actual builder is cross-platform Python (works on Windows too):
#   python3 installer/build_pyz.py
exec python3 "$(dirname "$0")/build_pyz.py" "$@"
