#!/usr/bin/env python3
"""Package memory-atlas as a single self-contained .pyz (stdlib only, zero deps).

Cross-platform replacement for build-pyz.sh — works on macOS / Linux / Windows:

    python3 installer/build_pyz.py

Produces dist/memory-atlas.pyz, runnable anywhere with `python3 memory-atlas.pyz`.
"""
import os
import shutil
import sys
import tempfile
import zipapp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    stage = tempfile.mkdtemp(prefix="atlas-pyz-")
    try:
        # generator -> importable module (drop the shebang line so import is clean)
        with open(os.path.join(ROOT, "memory-atlas"), encoding="utf-8") as f:
            src = f.read().split("\n", 1)[1]
        with open(os.path.join(stage, "memory_atlas.py"), "w", encoding="utf-8") as f:
            f.write(src)
        shutil.copy(os.path.join(ROOT, "installer", "__main__.py"),
                    os.path.join(stage, "__main__.py"))

        # bundled resources (paths match __main__.py's extract prefixes)
        shutil.copy(os.path.join(ROOT, "memory-atlas.template.html"),
                    os.path.join(stage, "template.html"))
        d3 = os.environ.get("ATLAS_D3") or os.path.join(ROOT, "vendor", "d3.v7.min.js")
        if not os.path.isfile(d3):
            sys.exit(f"d3 missing: {d3}")
        shutil.copy(d3, os.path.join(stage, "d3.v7.min.js"))
        shutil.copytree(os.path.join(ROOT, "demo"), os.path.join(stage, "demo"))

        os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
        out = os.path.join(ROOT, "dist", "memory-atlas.pyz")
        zipapp.create_archive(stage, out, interpreter="/usr/bin/env python3",
                              compressed=True)
        # the interpreter line only matters for direct ./execution on unix;
        # on Windows you run `py memory-atlas.pyz` and it is ignored
        if os.name != "nt":
            os.chmod(out, 0o755)
        print(f"built: {out} ({os.path.getsize(out) // 1024}K)")
    finally:
        shutil.rmtree(stage, ignore_errors=True)


if __name__ == "__main__":
    main()
