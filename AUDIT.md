# memory-atlas v2.0.0 — полный аудит + драфты (handoff для чистой build-сессии)

**База:** коммит `a3db79c` (Mac push 07-08 22:51, arch:backups/memory-atlas.git), клон `~/memory-atlas`.
Все line-refs — из этой версии. Прочитано целиком: генератор (974 стр.) + template (2897 стр.).
**Стройки в этой сессии нет** — документ = аудит + предложения. Билдер: перед графиками dash читать skill `dataviz`; перед вёрсткой — `frontend-design` по вкусу.

---

## 0. Merge-протокол с Mac-сессией (живая 371e4348)

Mac прямо сейчас правит: **(а)** лейбл-каша на зуме (collision-cull, подложки, один кегль на всех — grid-скрин), **(б)** drag-перф 60→10fps при selected+ego·blur, **(в)** «имена в панели не кнопки». Её зоны в template:
- лейбл-блок `paintFrame` (~2531–2610), `drawTile`/`TILE_K`/`DESC_K` (~2613–2659), `drawFocus` (~2251–2263), `pick`/labelHits (~1083–1099).

Правило для билдера: эти диапазоны **принимает от Mac** (rebase на её следующий пуш), свои правки — новыми блоками + фиксы вне зон. Ветка в bare: не main; merge в main после её пуша.
«Раст?» всплывал дважды — вердикт Mac (подтверждаю по коду): **не язык, per-frame пересчёт** (см. §7). Зафиксировать, чтобы не всплывало.

---

## 1. Баги — severity-ranked (файл:строка · суть · фикс)

### Реальные логические

**B1 · generator:176 · `orphan` перевирает feedback-зону.** `orphan = not in_light and not in_heavy and not top` — нота, индексированная ТОЛЬКО в FEEDBACK_INDEX.md, получает `zone=feedback` (фикс 07-06), но `orphan=True` — fb_idx в флаге не участвует. Browse-тайл «orphan» и бейджи перевирают на ~80 нот. Тот же класс бага, что «81 unindexed» до 07-06 — недочинен. Фикс: `and stem not in fb_idx`. Тест на это добавить.

**B2 · template:2471 · pin-контракт ломается под поиском.** `globalAlpha = dimmed(n) ? 0.10 : pinDimmed(n)…` — dimmed() включает query/tags/isolate/maxN и бьёт ПЕРВЫМ: запиненная нода, не матчащая поиск, гаснет до 0.10. Контракт «pins остаются яркими» (context delivery) нарушен всеми фильтрами. Фикс: pinned (и selected) исключить из dimmed либо порядок веток.

**B3 · template:2218 · preset утекает в слои навсегда.** `applyPreset('meaning')` делает `hiddenKinds.delete('semantic')` + saveCfg → semantic-слой остаётся включённым после ухода с пресета, до ручного клика. Пресеты мутируют персистентное состояние без отката. Фикс-драфт: pre-preset snapshot слоёв, «—» в селекте = вернуть; или пресет не трогает hiddenKinds персистентно (сессионный override).

**B4 · template:1857 · `helpReset` сносит ЧУЖИЕ корпуса.** Wipe по префиксу `atlas:` убивает localStorage и bastra-атласа (пины/user-рёбра/теги — ручной труд). Фикс: скоуп до `KEYP` + отдельно спросить про общий `atlas:editor`.

**B5 · generator:549–563 · `--search-vecs --no-semantic-cross` = тихий ноль.** Фетч эмбеддингов, `_vecs_payload` И `semantic_layout` живут внутри `if semantic_cross` — выключил детектор → потерял и клиентский поиск, и semantic-раскладку, без warn. Фикс: фетчить если `search_vecs or semantic_cross`; layout считать при любом наличии vecs.

**B6 · template:2816 · browse-wikilinks дохнут пачками.** Регекс `\[\[([a-z0-9_-]+)\]\]` не знает `[[x|alias]]`, верхний регистр, кириллицу, `~2`-суффиксы. Генератор (WIKILINK_RE:61 + norm:65) принимает всё это → в превью тела половина ссылок рендерится как dead/сырой текст. Фикс: зеркалить генераторную семантику (pipe-alias, norm() порт уже есть рядом в форме `.toLowerCase().replace(...)` — унифицировать честно).

**B7 · generator:202–221 · ссылки на индекс-файлы рождают ghost-долги.** MEMORY.md/MEMORY-work.md/FEEDBACK_INDEX исключены из нод, но `[[MEMORY-work]]`/`[x](MEMORY.md)` из тел нот резолвятся в ghosts «memory_work» и т.п. — ложный «стоит написать». Фикс: стемы INDEX_FILES → skip (ни ребра, ни ghost'а), тест.

**B8 · template:2819 · XSS-класс в browse-md.** `[t](url)` вставляет `$2` в `href` после besc — кавычка не вырвется, но `javascript:…` проходит. Свой корпус — риск низкий; `--data` от внешних билдеров — уже поверхность. Фикс: allowlist схем (`https?:`, `#`), иначе рендер плейн-текстом.

**B9 · template:1735–1748 · `applyView` не персистит.** Меняет hiddenZones/hiddenKinds/color/size/layout, но saveCfg не зовёт → reload после применения вида возвращает старые слои. Плюс старые views без `layout` — камера летит в координаты чужой раскладки (guard есть только на смену, не на отсутствие: v.layout undefined → камера применяется как есть). Фикс: saveCfg в конце applyView; нет v.layout → применять только фильтры + toast.

**B10 · template:469–470 · browse-шапка врёт всегда.** `#bpath` захардкожен `~/memory`, `.who` — `zzalli@mac · self-audit`. Никогда не обновляются из DATA (src есть!). На Арче — двойная ложь. Фикс: `bpath = DATA.src`, who — из DATA (генератору эмитить `host` = `platform.node()`), или убрать.

### Поведенческие / полировка

**B11 · template:867 · magnet+particles автостартуют с бута.** `Object.assign(toggles, CFG.toggles, {gestures:false})` — вебка исключена, а motion-режимы нет: включил магнит раз — он навсегда в буте (постоянный rAF-луп). Фикс: восстанавливать только статические тоглы; magnet/particles/gestures = session-only.

**B12 · template:2885 · deep-link `?node=` при cam=stay показывает не ноду.** focusNode → selectNode(noFly) → stay → камера остаётся на стартовом fit; панель открыта, нода где-то. Deep-link = явный интент «покажи» → форсить frameEgo независимо от stay (как Enter в поиске).

**B13 · template:2875 · `TS===1` неотличим от легаси.** `if (CFG.TS && CFG.TS !== 1)` — магическое значение вместо версии конфига. Практически недостижимо шагом 0.15 от 1.25, но правильный фикс: `cfg.v: 2` и явная миграция, магию убрать.

**B14 · template:1221 · мёртвый селектор `[data-openned]`** рядом с живым `[data-opened]` — мусор от старой правки, убрать.

**B15 · template:896 + 1605 · pins-сватчи стареют.** colorMode change перерисовывает легенду (1466), но не пины — кружки в pins-карте остаются в старом цвете до следующей мутации пинов. Однострочный `renderPins()` в хендлер.

**B16 · generator:397 · docstring врёт про таймаут.** `_ollama_up(timeout=3)`, комментарий «1s-класс». Косметика, но это healthcheck-подпись — поправить.

**B17 · template:2381–2388 · onScr-луп бежит и в ego-проходе.** Плотность считается по всем нодам до `const autoF = only ? 1 : …` — в only-проходе результат выбрасывается. Вынести под `if (!only)`. (Микро; но в drawFocus paintFrame бежит дважды за кадр — см. §7.)

**B18 · template:1976 · magnetStep итерирует все ноды всегда.** Даже при выключенном магните — decay-луп по 400+ нодам на каждый draw. Ранний выход при `!toggles.magnet && !magActive`.

**B19 · search: два разных «поиска».** Канвас-фильтр `matches()` (1294) ищет по id/label/desc/type/zone; дропдаун (1300) — ещё и по телу (tier 2). Юзер видит хит в дропдауне, канвас его дымит. Связать: query-фильтр учитывает body-матч (кэш lowercased-тел строится один раз на буте — заодно уберёт indexOf по 1MB на каждый keypress).

**B20 · generator:135–139 + 186 · стем-коллизия: второй файл недостижим по [[ссылке]].** `a-b.md` и `a_b.md` → второй = `a_b~2`, но lookup оставляет `a_b` за первым — все wikilinks ведут в первый. Warn есть; в дашборд/доку добавить как «коллизии» сигнал (n сейчас = 0 на обоих корпусах? проверить прогоном).

**B21 · hulls включают ghosts** (2295: filter по visible, ghost проходит) — пунктирные ноды-фантомы растягивают контур зоны. Решение спорное (ghost унаследовал зону референта — место осмысленно); минимум — задокументировать, максимум — `&& !n.ghost` и посмотреть глазами.

**B22 · зоны 1-8 хоткеи глухи к пустым зонам** (1435: zoneOrder без фильтра по счёту) и **зоны >8 падают в OTHER-серый** (831). Для memory-корпуса ок (6 зон); для `--data` — задокументировать контракт «≤8 зон с цветом».

---

## 2. Генератор — прод-гэпы (не баги)

**G1 · Портабельность (Арч = второй прод-хост).**
- `DEFAULT_SRC` = `~/.claude/projects/-Users-zzalli/memory` (:51) — на Арче мёртв. Фикс: список кандидатов `[-Users-zzalli, -home-zzalli]` → первый существующий; или `platform`-свитч.
- `open` (:723) → `xdg-open` на Linux: `"open" if sys.platform == "darwin" else "xdg-open"`.
- `~/.mac-claw/atlas/` — имя кривое, но дир существует на ОБОИХ хостах (канал синка) — оставить, задокументировать в README.
- Арч-факты для билдера: python3 ✓, chromium ✓ (headless smoke), ollama 0.20.2 ✓ жив (`nomic-embed-text` наличие проверить: `ollama list | grep nomic`, нет → `ollama pull nomic-embed-text`), d3-кэша НЕТ (один curl из :631), корпус = 288 нот `~/.claude/projects/-home-zzalli/memory`, memory-git есть (detect_session заработает).

**G2 · Frontmatter-парсер vs эталон-формат вульта.** `type:`/`tier:`/`part_of:`/`session:` матчатся ТОЛЬКО с отступом (`^\s+`, :79–82), `tags:` тоже (:87) — top-level `type:` молча даёт `?`. reference_vault_format допускает больше ключей; главное упущение — **`metadata.state`** (superseded/transition, proj_vault_state_layer) не читается вовсе → см. §9.1. Фикс парсера: паттерны `^\s*key:` (оба уровня), + `state`.

**G3 · emb-cache растёт вечно** (:406–445): sha-ключи старых версий тел не выселяются. После успешного прогона — прунить ключи вне `keys.values()` текущего корпуса (одна строка + тест).

**G4 · `--data` без валидации контракта** (:682) — битый JSON от внешнего билдера = криптик-ошибка в template. Мини-валидатор: nodes[].id/zone/label присутствуют, edges ссылаются на существующие id (или ghost), понятный exit.

**G5 · Version handshake.** VERSION живёт только в генераторе; стейл симлинк template = тихая каша. Драфт: `TPL_V` в template (`<meta name="tpl-v" content="N">`), генератор грепает и warn при рассинхроне. Дёшево, ловит реальный клас с двумя хостами.

**G6 · regen-команда без квотинга** (template:1832): `--src` с пробелом ломает копипасту. `shlex.quote`-эквивалент на JS-стороне (обернуть в одинарные при недоверенных символах).

**G7 · EXCLUDE_DIRS** (:54): нет `.obsidian`, `node_modules`, `.trash` — для чужих вультов (portable-мечта) добавить.

**G8 · heat = линейный age** (:224–226): одна древняя нота сжимает весь корпус к 1.0. Драфт: rank-based (как timeline :2133) или лог-шкала — сравнить глазами на реальном корпусе, выбрать по виду.

**G9 · detect_tag_overlap асимметрия** (:278 `m["id"] <= n["id"]`) — top-k видит только «старших» соседей; это graph-lab verbatim (задокументированная их кривизна) — НЕ чинить молча, отметить в докстринге явнее.

**G10 · to_browse_data `mtime: 0`** (:605) для реальных нот — сорт по дате в browse невозможен. Прокинуть настоящий.

---

## 3. Инвентарь настроек — «все связать» (ядро аска)

Полная карта ручек as-is. П = персист (localStorage cfg), Л = deep-link, Э = экспортируемо.

| Ручка | Где | П | Л | Дыра |
|---|---|---|---|---|
| colorMode / sizeMode | HUD | ✓ | ✓ `?color/size` | — |
| focusMode (dim/blur/tiles) | HUD | ✓ focus2 | ✗ | |
| labelMode + hops | HUD | ✓ | ✗ | |
| camPolicy | HUD | ✓ camPolicy2 | ✗ | |
| layout | HUD | ✓ | ✓ `?layout` | |
| taskPreset | HUD | эфемерн | ✗ | мутирует слои НАВСЕГДА (B3) |
| maxN / edgeAlpha / nodeSize | HUD | ✓ | ✗ | |
| toggles ×12 | HUD | ✓ | ✗ | motion автостарт (B11) |
| TS (A±) | bar | ✓ | ✗ | магия TS=1 (B13) |
| hiddenZones / hiddenKinds | chips | ✓ | ✗ | |
| tagSel / isolate | tags/legend | ✗ | ✗ | вид не восстановим |
| pins | RMB | ✓ | ✗ | гаснут под фильтрами (B2) |
| views | card | ✓ | ✗ | частичная схема (см. ниже) |
| userTags / zoneOverride | panel | ✓ | ✗ | экспорта нет |
| overlay (user-рёбра/negatives) | canvas | ✓ | ✗ | export есть, **import НЕТ** |
| editorPref | help | ✓ глобал | ✗ | шарится между корпусами молча |
| q / node / zoom | — | ✗ | ✓ | `?node` + stay (B12) |

Три системные дыры:
1. **Нет import** — весь ручной труд (user-рёбра, negatives, теги, пины, виды) заперт в одном браузере одного хоста. Export только overlay.
2. **«Вид» недоспецифицирован**: views хранят камеру+слои+color/size/layout, но НЕ edgeAlpha/nodeSize/maxN/labelMode/focus/tagSel/isolate — восстановленный вид выглядит иначе. Решить, что такое view (моё предложение: полный снапшот cfg + фильтры + камера; версионировать `{v:2}`).
3. **Пресеты и виды не дружат**: пресет = мутация без отката, вид = частичный снапшот. Унифицировать: preset = builtin-view (та же машинерия применения, transactional).

## 4. Драфт: settings-sheet + профиль

HUD остаётся quick-controls. Новый ⚙-sheet (тот же glass, esc-каскад, hint-механика `data-hint` уже есть):
- **Секции:** Вид (color/size/labels/TS) · Камера (policy/lockZoom/зум-пределы) · Слои (zones/kinds/ghosts/hulls/clusters) · Поведение (magnet/particles/gestures/collide/softFade — с пометкой «не персистятся») · Данные (regen-билдер сюда из отдельной модалки; возраст данных) · Профиль · Редактор.
- **Профиль export/import**, схема:
```json
{ "v": 1, "kind": "atlas-profile", "title": "memory-atlas", "exported": 1720000000,
  "cfg": {"color": "...", "toggles": {}, "...": "..."},
  "pins": ["id"], "views": [{"v": 2, "name": "...", "...": "..."}],
  "userTags": {"id": ["tag"]}, "zoneOverride": {"id": "zone"},
  "overlay": {"edges": [], "negatives": []} }
```
  Import = merge (не replace): stale id-refs скипаются со счётчиком (паттерн overlayStale:721 уже есть). Кнопки: экспорт всего / импорт / reset-корпуса (скоупленный, B4).
- **Deep-link `?state=`** = base64(JSON срез cfg+фильтры+камера) — полный вид шарится между хостами одной строкой. Существующие короткие параметры остаются.

## 5. Драфт: dash-таб («▦ dash», третья вкладка)

Пульт над корпусом, без новой логики — всё wired в существующие механизмы. Стиль = glass-HUD (не Catppuccin browse). Билдеру: читать `dataviz` ПЕРЕД графиками.

| Тайл | Данные (клиент, из DATA) | Клик → |
|---|---|---|
| KPI-строка | ноты/рёбра/ghosts/orphans/conflicts/кластеры/медиана age/v+generated | — |
| Зоны | bar по zoneOrder (счёт/свежесть) | graph + isolate зоны (`toggleZone`-механика) |
| Свежесть | гистограмма age_days, canvas | `applyPreset('fresh')` |
| **Ghost-долги** | топ ghost по in-degree + список реферреров | `focusNode(ghost)` — actionable «стоит написать» |
| Хабы | топ-10 degree | `focusNode` |
| Orphans / conflicts | списки (после B1!) | `openInBrowse(id)` |
| Детекторы | счёт per-kind + переключатели слоёв | shared `hiddenKinds` |
| Здоровье данных | age данных, overlayStale, stem-коллизии (G-эмит), hidden nodes | ⚙ regen |

Деградация: `--data`-корпуса без нужных полей → тайл скрыт, не падение (паттерн browse-вкладки :2715).

## 6. Портабельность/деплой Арч (чеклист билдеру)

1. G1-фиксы → `memory-atlas --self-test` (расширить: platform-детект, frontmatter top-level, B1/B7 кейсы).
2. `curl -Lo ~/.mac-claw/atlas/d3.v7.min.js https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js`
3. Симлинки `~/bin/memory-atlas{,.template.html}` → `~/memory-atlas/` (схема Mac; ~/bin вне dotfiles-whitelist).
4. Прогон на 288 нот; smoke: `chromium --headless --dump-dom file://…/memory-atlas.html | grep data-ready`.
5. Playwright-глаза: вкладки graph/browse/dash, KPI-клик → изоляция, профиль export→import→toast, скриншоты.
6. Git: ветка `arch-prod-v21` → push в bare; merge в main ТОЛЬКО после пуша Mac (см. §0).

## 7. Перф — сверка для Mac-зоны (НЕ строить здесь)

Корень 60→10fps (подтверждаю по коду): `drawFocus` (:2251) на КАЖДЫЙ кадр драга гонит `paintFrame(bgCtx, {muted:true})` — полный проход графа в offscreen (включая hulls!) + blur-blit, затем второй paintFrame (ego). Итого 2×O(nodes+edges)+фильтр на кадр.
Фикс-скетч (если Mac не докрыла): bg-снапшот кэшируется, инвалидация по {transform, sim-tick, data-мутация}; драг ego-ноды фон НЕ меняет (она рисуется в резком проходе) → блит из кэша. Дополнительно моё: B17, B18, quadtree для `pick`/near/magnet (d3.quadtree уже в бандле) — но только ПОСЛЕ её пуша, на её коде.

## 8. Тест-план (для build-сессии)

- Self-test: +B1 (fb-orphan), +B7 (index-ghost), +G2 (top-level type), +G3 (prune), +G4 (валидатор), +B5 (vecs при no-semantic).
- Headless-smoke расширить: `data-ready` + dash-маркер + отсутствие console errors (`--enable-logging`).
- Playwright-сценарий: полный клик-обход (вкладки, пресеты — проверить B3-откат, view save/apply — B9-персист, профиль roundtrip, `?state=`-линк).
- Регресс глазами: скриншоты force/pack/ring/timeline до/после — раскладки не должны сдвинуться (мои правки вне layout-кода).

## 9. x20-направления (ranked, с якорями в твоих проектах)

1. **STATE-слой** (стыкуется с proj_vault_state_layer, ревью 07-14): генератор читает `metadata.state` → superseded = гашеная нода/крест, transition = полупрозрачная; dash-тайл «ghost memory» = счёт+список. Атлас становится ВИЗУАЛЬНЫМ сканером призраков — vault-state получает глаза, atlas получает смысловой слой. Дешёво: один ключ парсера + рендер-стиль + тайл.
2. **Fire-log heat** для memory-корпуса (как в bastra-модуле: heat=reach из `~/.claude/ida/fire-log.jsonl`): второй heat-режим «recall-тепло» рядом с freshness — «что recall реально трогает» ≠ «что свежее». Данные уже есть, полярность решает билдер (DATA CONTRACT это допускает: :35).
3. **Diff-режим**: `--diff old.json` → new/changed/dead ноды подсвечены; закрывает «что изменилось с прошлой пересборки» (сейчас только `generated`-штамп). Экспорт full JSON уже есть — половина механики готова.
4. **Session-родословная**: `originSessionId` уже парсится (:82) — color-mode «session» + dash-тайл «крупнейшие сессии-истоки». Микростоимость.
5. **Отвергнуто, с причинами** (чтобы не всплывало): Rust/WebGL-рендер — стена не язык (§7); multi-corpus в одном html — против bellard, корпус = файл; 3D — юзер явно отверг 07-07.

## 10. Открытые вопросы билдеру (решить в build-сессии)

- B21 (ghosts в hulls): чинить или задокументировать — смотреть глазами.
- G8 (heat-шкала): rank vs log — глазами на реальном корпусе.
- editorPref: оставить глобальным или per-corpus.
- «view» = полный снапшот? (моя рекомендация — да, v2-схема, §3.2).
- dash: свой хоткей (`g`?) и место в esc-каскаде.
