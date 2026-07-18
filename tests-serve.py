#!/usr/bin/env python3
"""Живая проверка слитых фич: 409, force, гарды, атомарность. Реальный сервер, реальный HTTP."""
import json, os, subprocess, sys, tempfile, time, urllib.request, urllib.error, shutil

SERVE = os.path.expanduser("~/src/memory-atlas/atlas-serve")
PORT = 8791
vault = tempfile.mkdtemp(prefix="atlas-test-")
os.makedirs(os.path.join(vault, "raw"), exist_ok=True)
os.makedirs(os.path.join(vault, ".obsidian"), exist_ok=True)
open(os.path.join(vault, "alpha.md"), "w").write("---\ntitle: Alpha\n---\n\n# Alpha\n\nbody one\n")
open(os.path.join(vault, "raw", "src.md"), "w").write("raw source\n")
open(os.path.join(vault, ".obsidian", "cfg.md"), "w").write("cfg\n")
open(os.path.join(vault, "atlas.html"), "w").write("<html>stub</html>")

srv = subprocess.Popen([sys.executable, SERVE, "--vault", vault, "--atlas",
                        os.path.join(vault, "atlas.html"), "--port", str(PORT)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
time.sleep(1.5)

def call(method, path, payload=None):
    url = f"http://127.0.0.1:{PORT}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")

fails = []
def check(name, got, want):
    ok = got == want
    print(f"  {'OK  ' if ok else 'FAIL'} {name}: {got}" + ("" if ok else f"  (ждали {want})"))
    if not ok:
        fails.append(name)

try:
    print("— чтение отдаёт mtime")
    c, r = call("GET", "/api/note?path=alpha.md")
    check("read 200", c, 200)
    mt = r.get("mtime")
    check("mtime присутствует", isinstance(mt, int) and mt > 0, True)

    print("— запись со свежим mtime проходит")
    c, r = call("POST", "/api/save", {"path": "alpha.md", "body": "body two\n", "mtime": mt})
    check("save 200", c, 200)
    mt2 = r.get("mtime")

    print("— запись с УСТАРЕВШИМ mtime отбивается (было бы молчаливой потерей правки)")
    c, r = call("POST", "/api/save", {"path": "alpha.md", "body": "clobber\n", "mtime": mt - 99})
    check("stale save 409", c, 409)
    check("тело не затёрто", open(os.path.join(vault, "alpha.md")).read().strip().endswith("body two"), True)

    print("— force продавливает сознательно")
    c, r = call("POST", "/api/save", {"path": "alpha.md", "body": "forced\n",
                                      "mtime": mt - 99, "force": True})
    check("force 200", c, 200)
    check("тело перезаписано", open(os.path.join(vault, "alpha.md")).read().strip().endswith("forced"), True)

    print("— без mtime пишет как раньше (обратная совместимость клиента)")
    c, _ = call("POST", "/api/save", {"path": "alpha.md", "body": "legacy\n"})
    check("no-mtime 200", c, 200)

    print("— гарды вульта")
    c, r = call("POST", "/api/save", {"path": "raw/src.md", "body": "x"})
    check("raw/ 403", c, 403)
    c, r = call("POST", "/api/save", {"path": ".obsidian/cfg.md", "body": "x"})
    check("dotfile 400", c, 400)
    check("raw цел", open(os.path.join(vault, "raw", "src.md")).read().strip(), "raw source")
    c, r = call("POST", "/api/save", {"path": "../escape.md", "body": "x"})
    check("escape отбит", c in (400, 403), True)

    print("— атомарность не оставляет мусора")
    leftovers = [f for f in os.listdir(vault) if f.endswith(".atlas-tmp")]
    check("нет .atlas-tmp", leftovers, [])

finally:
    srv.terminate()
    try: srv.wait(timeout=5)
    except subprocess.TimeoutExpired: srv.kill()
    shutil.rmtree(vault, ignore_errors=True)

print()
print("ПРОВАЛЫ:", fails if fails else "нет")
sys.exit(1 if fails else 0)
