#!/usr/bin/env bash
# Package memory-atlas as a single self-contained .pyz (stdlib only, zero deps).
# Produces dist/memory-atlas.pyz — one file anyone can run with `python3 memory-atlas.pyz`.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

# generator -> importable module (drop the shebang line so import is clean)
tail -n +2 "$ROOT/memory-atlas" > "$STAGE/memory_atlas.py"
cp "$ROOT/installer/__main__.py" "$STAGE/__main__.py"

# bundled resources (paths match __main__.py's extract prefixes)
cp "$ROOT/memory-atlas.template.html" "$STAGE/template.html"
D3="${ATLAS_D3:-$ROOT/vendor/d3.v7.min.js}"
[ -f "$D3" ] || D3="$HOME/.mac-claw/atlas/d3.v7.min.js"
[ -f "$D3" ] || { echo "d3 cache missing: $D3" >&2; exit 1; }
cp "$D3" "$STAGE/d3.v7.min.js"
cp -R "$ROOT/demo" "$STAGE/demo"

mkdir -p "$ROOT/dist"
python3 -m zipapp "$STAGE" \
  -o "$ROOT/dist/memory-atlas.pyz" \
  -p "/usr/bin/env python3"
chmod +x "$ROOT/dist/memory-atlas.pyz"
echo "built: $ROOT/dist/memory-atlas.pyz ($(du -h "$ROOT/dist/memory-atlas.pyz" | cut -f1))"
