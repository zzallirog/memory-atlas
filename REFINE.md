# REFINE — прогон 2026-07-09 (Arch/Fable, ветка `refine-20260709`)

Поколение N+1 относительно `AUDIT.md` (base a3db79c): стартовал с прошлого ledger'а,
шёл диффом по свежей поверхности (0dbef98..cf3d0cc: i18n / installer / LOD / public-release)
+ gh-паблиш 9bb334d. Метод: logic-flaw-audit (harvest → confront-probe → reproduce-or-discard).
Каждая находка — с воспроизводимым probe; фиксы прогнаны через self-test (36→39) +
headless data-ready на demo / demo-pyz / demo-en / real-корпус (405 нод).

## Починено в этом прогоне

- **R1 · ② граница · session-детектор мёртв для vault-в-поддиректории git-репо.**
  `git -C src log --name-only` отдаёт пути от КОРНЯ репо, `node_by_rel` — от `--src` →
  0 совпадений, тихий ноль. Demo это воспроизводил (пути `demo/cooking/…` vs `cooking/…`).
  Фикс: `--relative` (+ фильтрация к src бесплатно). Тест: живой git-репо в tempdir,
  vault в поддире, co-touch коммит → ребро есть.
- **R1a · сиблинг, вскрыт фиксом R1 (fix = проявитель):** demo из клона начал тащить
  **59** фейковых session-рёбер из НАШИХ упаковочных коммитов (12+ файлов разом), при
  этом pyz-demo (без git) — 0. Тот же класс шума, из-за которого `--demo` глушит temporal
  → `--demo` теперь глушит и session. Demo-мосты снова честные: shared_ref=3 + tag=1.
- **R2 · ① замер/лог · G4: битый `--data` = exit 0 + мёртвая страница.** Probe: edge на
  несуществующую ноду → HTML без `data-ready`, генератор молчит. Фикс: `validate_data()`
  (nodes[]/id/дубликаты/endpoints) + понятный JSONDecodeError; exit 1 с точным адресом
  ошибки. Тест на 4 битых формы. ⚠ `memory-atlas-bastra` (Mac-модуль) на Арче нет —
  прогнать его пайп через валидатор после синка на Mac.
- **R3 · ⑥ i18n · 6 из 7 preset-тостов НЕ обёрнуты в `T()`** при живых переводах в словаре
  (обёрнут был только `overview`) → EN-режим показывал RU-тосты. Drift-guard-тест это не
  ловит by-design (сканит только статик-маркап до i18nEN, не JS-литералы). Фикс: T() ×6;
  probe: байтовая сверка ключей со словарём — 7/7, raw-RU-тостов 0.
- **R4 · ④ время · maxN «all» персистился абсолютным числом.** Корпус вырос → сохранённый
  N < realCount → после пересборки граф молча top-N-фильтрован. Фикс: «all» = `null`-сентинел.
  Каверат: старые cfg с абсолютным N не мигрируются (отличить «юзер выбрал 324» от
  «324 было all» нельзя) — one-off, чинится ползунком.
- **R5 · ⑤ дисциплина · клиентский semantic-поиск хардкодил `127.0.0.1:11434`,** игнорируя
  `ATLAS_OLLAMA`, которым строился граф. Фикс: генератор эмитит `vecs.url`, клиент его чтит.
  Каверат (осознанный): нестандартный URL уезжает в HTML — тот же класс приватности, что
  сами vecs; для shared-HTML документировано «regenerate, don't reshare».
- **R6 · потомок 7589d17 · мёртвый edge-hover код.** Коммит убрал pick/highlight рёбер, но
  оставил `pickEdge`/`tipEdge`/`hoveredEdge`/CSS `.ekind` (~35 строк) — удалены. NB: вместе
  с highlight'ом тогда умер и edge-TOOLTIP (kind/score по ховеру) — если захочется вернуть,
  тултип без подсветки не фликерит (фликерила отрисовка); сейчас инфо о ребре живёт в
  панели ноды (kdot+score) и чипах.
- **R7 · G5 · version handshake генератор↔шаблон.** Пара деплоится симлинками на 2 хостах,
  stale-половина = тихая каша. Фикс: `<meta name="atlas-tpl" content="VERSION">` + warn
  генератора при skew (probe: старый шаблон → «marker missing vs 2.4.1») + self-test
  жёстко требует бампить метку вместе с VERSION.
- **R8 · паблиш-поверхность расщепила source-of-truth.** LICENSE / docs/QUICKSTART.md /
  docs/shots / публичный README жили ТОЛЬКО на github (squash 9bb334d) — дев-репо о них
  не знал. Принято в дев-репо; README = публичный + секции Development/Changelog;
  локальный стейл-README (27 тестов, старые пути) ушёл. QUICKSTART-фикс: `--out` дефолт
  описан честно (cache-dir, не «next to the command»).
- **R9 · installer · `.pyz` без компрессии:** `zipapp.create_archive(compressed=True)`
  → 590K → 195K; pyz-run перепроверен.
- **R10 · exportJSON тащил в экспорт кадровый мусор** `_tm` (tile-метрики) и `_la` — срезаны.
- VERSION 2.4.0 → **2.4.1**, changelog в README.

## Positive confronts (проверено и ДЕРЖИТ)

- CI на gh: последний run на 9bb334d **success** (badge честный); матрица реально гоняет
  self-test+demo+pyz на 3 ОС.
- B1/B2/B3/B7/B8/B9/B13/B15/B19/B21/B23/B24 из AUDIT.md — фиксы живы в коде (line-probes);
  B3 решён красиво: `sessionKinds` session-override, persist-truth не мутируется.
- Демо/pyz паритет: 24 ноды / 43 ребра / data-ready=1 оба пути; EN-локаль строится и живёт.
- Реальный корпус: 405 нод / 3132 ребра / 4.7s / data-ready=1; console clean.
- py3.8-флор держит (endswith-фикс cf3d0cc; нового 3.9+ синтаксиса не внесено).
- i18n drift-guard тест честно ловит статик-маркап (36→39 тестов все зелёные).

## Найдено, НЕ чинено (осознанно; кандидаты следующего прогона)

- **N1 · `?state=` из чужой ссылки персистит слои**: boot применяет hz/hk в живые Set'ы,
  первый же saveCfg (любой клик) записывает их в cfg навсегда. Согласуется с семантикой
  applyView («вид персистит»), но deep-link ≠ view: чужая ссылка молча перезаписывает мои
  слои. UX-решение класса B3/S4 — решить, потом строить (session-запуск слоёв?).
- **N2 · G3 emb-cache** — бессрочный рост, per-src/LRU требует смены формата (в AUDIT
  корректно помечен «не однострочник», прошлый наивный фикс был бы cross-corpus регрессией).
- **N3 · pyz self-test**: `--self-test` изнутри .pyz упадёт (тесты читают шаблон по
  `__file__`, не через `ATLAS_TEMPLATE`). CI гоняет из сорцов — латентно; документировать
  или прокинуть env в 2 тестах.
- **N4 · esc в browse-табе** не возвращает в graph (dash возвращает) — асимметрия каскада.
- **N5 · dash «stem-коллизии» ищет `~` в id** — нота с литеральной `~` в имени = false
  positive; честнее эмитить коллизии генератором в DATA (AUDIT B20/S10 — так и предлагал).
- **N6 · `?zoom=` обходит scaleExtent** (программный transform d3 не клампит) — мелочь.
- **N7 · usage-легенда** «touched» — EN-литерал в RU-режиме (обратная дыра, минор).
- **N8 · dist/ на gh закоммичен, в дев-репо gitignored** — publish-флоу должен пересобирать
  и класть pyz при каждом паблише, иначе gh-pyz стухнет (сейчас: 2.4.0 vs код 2.4.1 после мержа).
- **N9 · словарные сироты**: ключи убитого edge-тултипа остались в i18nEN — безвредно, чистка
  при случае.

## Verify-протокол прогона

```
./memory-atlas --self-test                       # 39 green
./memory-atlas --demo --no-open --out $S/demo.html          # 24n/43e
python3 installer/build_pyz.py && python3 dist/memory-atlas.pyz --demo …
chromium --headless --dump-dom file://… | grep -ao 'data-ready="1"'   # ×4 билда
echo '{битый json}' | ./memory-atlas --data -    # exit 1, точный адрес
ATLAS_TEMPLATE=<old> ./memory-atlas --demo       # skew-warn
```
