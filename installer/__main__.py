"""zipapp bootstrap for memory-atlas.

Files bundled inside a .pyz can't be open()'d by filesystem path, so on startup
we extract the packaged resources (template, d3, demo vault) to a temp dir and
point the generator's env overrides at them. Running from a plain source dir
(no zip archive) is a no-op: the generator finds its siblings normally.
"""
import atexit
import os
import shutil
import sys
import tempfile
import zipfile


def _stage_resources():
    loader = getattr(sys.modules.get("__main__"), "__loader__", None)
    archive = getattr(loader, "archive", None)
    if not archive or not os.path.isfile(archive):
        return  # source-dir run — generator resolves its own siblings
    tmp = tempfile.mkdtemp(prefix="memory-atlas-")
    atexit.register(shutil.rmtree, tmp, ignore_errors=True)
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if name.startswith(("template.html", "d3.v7.min.js", "demo/")):
                z.extract(name, tmp)
    os.environ.setdefault("ATLAS_TEMPLATE", os.path.join(tmp, "template.html"))
    os.environ.setdefault("ATLAS_D3", os.path.join(tmp, "d3.v7.min.js"))
    os.environ.setdefault("ATLAS_DEMO", os.path.join(tmp, "demo"))


def main():
    _stage_resources()
    import memory_atlas
    memory_atlas.main()


if __name__ == "__main__":
    main()
