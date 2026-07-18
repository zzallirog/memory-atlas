#!/usr/bin/env python3
"""Apply tier-inference mapping to the flat vault, collision-safe.
Generator resolves part_of via norm(name)=lower+hyphen->underscore. A tier-B leaf
whose norm collides with a same-named spine theme is MERGED into that one node
(no ghost duplicate, no data loss). Backs up the vault first."""
import json, os, re, sys, shutil, unicodedata, time, collections

argv = [a for a in sys.argv[1:] if a != "--dry-run"]
DRY = "--dry-run" in sys.argv
MAP = argv[0] if len(argv) > 0 else os.path.expanduser("~/atlas-tier-demo/mapping.json")
VAULT = argv[1] if len(argv) > 1 else os.path.expanduser("~/atlas-tier-demo/vault")

def norm(k):  # identical to generator memory-atlas:151
    k = k.strip().lower().replace("-", "_")
    return k[:-3] if k.endswith(".md") else k

def slugify(t):
    """Имя файла из названия узла. Unicode СОХРАНЯЕМ: вульты бывают не латинские
    (целевой — украинский), а NFKD->ascii стирал кириллицу целиком и возвращал "term"
    для КАЖДОГО узла — 61 узел хребта схлопывался в один файл. Режем только то,
    что ломает файловую систему."""
    t = unicodedata.normalize("NFC", t).strip()
    t = re.sub(r'[/\\:*?"<>|\x00-\x1f]+', "-", t)   # запрещённые в FS
    t = re.sub(r"\s+", " ", t).strip(" .-")
    return t[:120] or "term"

# Зеркалит генератор memory-atlas:168-169 + :195-196 — `title:` это обсидиановое
# написание `name:`; без него чужой вульт даёт пустой индекс. `^\s*` — ключи бывают
# и вложенными (G2 в генераторе). name выигрывает, когда есть оба.
NAME_RE = re.compile(r'^\s*name:\s*(.+)$', re.M)
TITLE_RE = re.compile(r'^\s*title:\s*(.+)$', re.M)
FM_RE = re.compile(r'^---\n(.*?)\n---\n?(.*)$', re.S)

def read_note(path):
    raw = open(path, encoding="utf-8").read()
    m = FM_RE.match(raw)
    return (m.group(1), m.group(2)) if m else (None, raw)

def name_of(fmb):
    for rx in (NAME_RE, TITLE_RE):
        mm = rx.search(fmb or "")
        if mm:
            return mm.group(1).strip().strip('"\'')
    return None

def set_fields(fmb, **fields):
    lines = fmb.split("\n"); out = []; seen = set()
    for ln in lines:
        k = ln.split(":", 1)[0].strip() if ":" in ln else None
        if k in fields:
            out.append(f'{k}: {fields[k]}'); seen.add(k)
        else:
            out.append(ln)
    for k in fields:
        if k not in seen:
            out.append(f'{k}: {fields[k]}')
    return "\n".join(out)

def q(v): return '"' + str(v).replace('"', "'") + '"'

mapping = json.load(open(MAP, encoding="utf-8"))
spine, leaves = mapping["spine"], mapping["leaves"]

# backup (в dry-run не копируем — ничего не пишем)
stamp = time.strftime("%Y%m%d-%H%M%S")
bak = f"{VAULT.rstrip('/')}.bak-{stamp}"
if DRY:
    bak = "(dry-run, бэкап не делался)"
else:
    shutil.copytree(VAULT, bak)


def write(path, text):
    if not DRY:
        open(path, "w", encoding="utf-8").write(text)

# index existing notes by norm(name) — РЕКУРСИВНО. os.listdir видел только корень;
# в чужих вультах ноты лежат вложенно (например wiki/загальна/терміни/, 3 уровня),
# и плоский листинг находил 4 служебных файла вместо 2125 терминов: молчаливый ноль.
by_norm = {}
skipped_dirs = {".git", ".obsidian", "node_modules", "raw", ".trash"}
for root, dirs, files in os.walk(VAULT):
    dirs[:] = [d for d in dirs if d not in skipped_dirs and not d.startswith(".")]
    for fn in files:
        if not fn.endswith(".md"):
            continue
        p = os.path.join(root, fn)
        nm = name_of(read_note(p)[0]) or fn[:-3]   # без frontmatter — стем, как в генераторе
        by_norm.setdefault(norm(nm), p)

if not by_norm:
    sys.exit("ПУСТО: ни одной .md-ноты под %s — проверь путь до применения" % VAULT)

# куда класть материализованные узлы хребта: в папку, где живёт большинство листьев,
# иначе родители окажутся в другой зоне, чем дети
leaf_dirs = collections.Counter(os.path.dirname(p) for p in by_norm.values())
SPINE_DIR = leaf_dirs.most_common(1)[0][0] if leaf_dirs else VAULT

n_indexed = len(by_norm)   # снять ДО материализации хребта, иначе отчёт завышен на его размер
spine_norms = {norm(n["name"]) for n in spine}

# 1) materialize spine (merge into existing note if norm collides)
created = merged = 0
for node in spine:
    nm, tier, po = node["name"], node["tier"], node.get("part_of", "") or ""
    key = norm(nm)
    path = by_norm.get(key)
    if path:  # existing note (e.g. tier-B leaf 'aggression') becomes this spine node
        fmb, body = read_note(path)
        fmb = set_fields(fmb, name=q(nm), tier=tier, part_of=q(po))
        write(path, f"---\n{fmb}\n---\n{body}")
        merged += 1
    else:
        path = os.path.join(SPINE_DIR, slugify(nm) + ".md")
        gloss = node.get("gloss") or f"{tier}-tier taxonomy node: {nm}."
        fm = f'name: {q(nm)}\ntier: {tier}\npart_of: {q(po)}\nsource: spine-inferred'
        write(path, f"---\n{fm}\n---\n\n{gloss}\n")
        created += 1
    by_norm[key] = path

# 2) leaves: skip any whose norm IS a spine node (already set above); else set tier+part_of
leaf_set = 0; skipped_merged = 0; misses = []
for lf in leaves:
    term, tier, po = lf["term"], lf["tier"], lf.get("part_of", "") or ""
    key = norm(term)
    if key in spine_norms:  # this leaf == a spine node, already materialized
        skipped_merged += 1
        continue
    path = by_norm.get(key)
    if not path:
        misses.append(term); continue
    fmb, body = read_note(path)
    fmb = set_fields(fmb or "", tier=tier, part_of=q(po))   # нота без frontmatter — не падать
    write(path, f"---\n{fmb}\n---\n{body}")
    leaf_set += 1

total = sum(1 for _r, _d, _f in os.walk(VAULT) for fn in _f if fn.endswith(".md"))
print(("DRY-RUN — ничего не записано\n" if DRY else "") + f"backup: {bak}")
print(f"проиндексировано нот: {n_indexed}   узлы хребта пишутся в: {SPINE_DIR}")
print(f"spine: {created} created, {merged} merged-into-existing")
print(f"leaves: {leaf_set} set, {skipped_merged} merged-with-spine, {len(misses)} misses")
if misses: print("  MISSES:", misses[:20])
print(f"total notes now: {total}")

# Страховка от тихого нуля: раньше неверный путь/поле давали «успешный» прогон,
# который не трогал ни одной ноты и рапортовал сплошные misses.
if leaves and len(misses) > 0.5 * len(leaves):
    sys.exit("\nПРОВАЛ: %d из %d листьев не нашли ноту (>50%%). Скорее всего не тот "
             "путь до вульта или ноты именуются иначе. Ничего полезного не записано."
             % (len(misses), len(leaves)))
