# Atlas — cold-session handoff (2026-07-18, ~00:20)

Для холодной сессии / Fable. Всё исполнимо по анкорам ниже. Объяснения фич — прозой, не кавеманом.

## Контекст в одном абзаце
`memory-atlas` = вьювер+редактор графа знаний (single self-contained HTML + `atlas-serve` сайдкар).
Целевой юзер — **Миша** (нетех, украинский психо-глоссарий ~2300 терминов, плоский, ноль линков).
Корневой конфликт Миши: **«різний рівень задуму використання»** — тул построен как power-инструмент
(zzalli, 15 ручек в HUD), Мише нужен простой. Эта сессия: багфиксы + таксономия (#8) + интеракшн-
модель под два типа юзера (#9). Спека модели — `ROADMAP-STATE.md §#9`. Таксономия — `§#8`.

## Анкоры (проверено 2026-07-18 00:16)
- **Репо:** `/Users/zzalli/src/memory-atlas` · ветка **`feat/atlas-taxonomy-map`** (10 коммитов над `453ac91`, НЕ запушено).
- **Главные файлы:** `memory-atlas` (python-генератор) · `memory-atlas.template.html` (рантайм, ~416K, ОДНА длинная минифай-строка — grep нужен `-a`, правки через python-патчер с `assert count==1`).
- **Self-test:** `cd repo && python3 memory-atlas --self-test` → **48/48**. i18n-тест ЖЁСТКИЙ: каждая кириллическая строка в статичном markup (option/data-hint/title/text) нужна в `i18nEN` + `i18nUK`. Строки в JS `T('...')` — НЕ проверяются (рантайм).
- **Деплой на Арч (боевой тест):**
  1. `rsync -az memory-atlas.template.html arch:/home/zzalli/atlas-live/` (и `memory-atlas` если менял генератор)
  2. `ssh arch "bash -lc 'cd ~/atlas-live && python3 memory-atlas --src demo-v2 --no-open --out demo-atlas.html'"`
  - Serve: `atlas-serve --vault demo-v2 --atlas demo-atlas.html --port 8137` (127.0.0.1:8137, юзер смотрит там). `regen.sh` теперь БЕЗ `--no-detectors` (бэкап `regen.sh.bak-nodet`).
  - ⚠ `ssh arch` = **fish** → payload всегда в `bash -lc '…'` (heredoc/inline VAR= падают). Локальный Bash-tool = zsh.
- **Тест-вульт:** `arch:~/atlas-live/demo-v2/` зоны `терміни` + `проба-зона`. Демо-нота с телом: `терміни/nesvidome.md`.
- **Локальная верификация (hover-pins/граф работают на `file://`, БЕЗ сервера):**
  - `scratchpad/render_atlas.py` — headless Chrome CDP (порт 9337, изолир. профиль). Режимы: `<preset>` или `eval:<js>`.
    ⚠ порт **9222 занят ssh-туннелем к chromium Арча** — НЕ юзать 9222 для локального.
  - regen локального теста: `python3 memory-atlas --src psy=scratchpad/psy-vault --out scratchpad/psy.html --no-open --no-detectors`
  - пример: `python3 render_atlas.py psy.html out.png "eval:(function(){var n=nodes.find(x=>BODIES[x.id]); createHoverPin(n); return document.querySelectorAll('#hoverpins>div').length})()" 2600`
  - edit/tag/create-флоу требуют `atlas-serve` — на `file://` НЕ драйвятся (self-test их не покрывает).
- **Scratchpad артефакты:** `patch_*.py` (все врезки сессии), `_newcard.txt`/`_oldcard.txt` (createHoverPin), `nesvidome.md`, `render_atlas.py`, `ref-okf.png` (референс OKF OpenWiki — цель для reader-mode).

## Модель данных / код-локации (grep `-a` в template)
- Ноды: `{id,label,desc,zone,type,path,bytes,age_days,part_of,tier,tags,degree,heat}`. Рёбра: `{source,target,kind}` (kind: wiki/semantic/tag_overlap/temporal_proximity/session_co_occurrence/structural_homology/**part_of**).
- **browse = отдельный IIFE** (openNode/loadTags/setTags/mdRender/D — там). Граф-scope: `nodes/byId/BODIES/outLinks/inLinks/togglePin/createHoverPin/tipPlace/selectNode`. `mdRender` экспортнут в `window.mdRender` для граф-scope.
- Ключевое: `createHoverPin` (граф-scope) · `togglePin` · `tipPlace` (тултип, кламп за `#hud`) · `groupVal`/`groupKey` (ось `tier`) · `PRESETS`/`applyPreset` (пресет `taxonomy`) · CSS `#hud`(лев.панель) `#panel`(прав.бар z5 w330 right14).

## Что СДЕЛАНО этой сессией (живо на Арче)
- **#1** concept-extract работает в edit-mode textarea (был слеп `window.getSelection()`).
- **#3** related не пропадает — `regen.sh` без `--no-detectors` (semantic-рёбра переживают авто-синк).
- **#4** снятый в browse тег синкается в граф (`byId`/`bBy` в памяти + renderTags/requestDraw).
- **#5** dblclick входит в правку надёжно (пустая нота + игнор ссылок/контролов).
- **#8** таксономия: генератор эмитит membership-рёбра `kind=part_of` из `node.part_of`; рантайм — `tier` как ось groupMode + пресет `taxonomy` (dendro+tier+part_of). ⚠ ждёт разметку `tier:`/`part_of:` во frontmatter (демо psy-vault размечен, живой demo-v2 — нет).
- **#9** интеракция: pin-тост · hover-pin (2×rmb) = ПОЛНЫЙ клон правого бара (mdRender-тело+связи+кнопки, скролл, левее #panel = приоритет прав.бара) · шапка-клик будит · **драг за шапку** · rmb-pin **пан на текущем зуме** развязан от cam (cam=stay убивает LMB-ресайз, но НЕ rmb-move).

## ОЧЕРЕДЬ (task-пакет — детали в каждой)
См. TaskCreate-список этой сессии. Приоритет 1→N:
1. **reader-mode** (левокликеры): авто-скрыть `#hud` + растянуть `#panel` при select. Референс `scratchpad/ref-okf.png` (ноль лев.HUD, широкий прав.ридер). Класс `body.reader` + CSS. Развилка: auto-on-select vs toggle-кнопка. Юзер сказал «автоматом».
2. **hover polish**: прозрачность карточки ∝ зум (% видимости ноды) + fade когда `#panel` открыт (юзер: «правый бар приоритетнее, сдвигал/спадающе прозрачным»).
3. **snap-в-угол** при отпускании драга (магнит к 4 углам).
4. **#8 tier для живых 2300**: авто-инференс А/В/С (воркфлоу «3 опуса» — юзер сам предлагал) ИЛИ курация-UI. Плоский глоссарий иерархии не несёт.
5. **unify zone/cluster** («два режима зон → эмерджем в единый блок»). zone=папка(двигаешь), cluster=louvain(авто). Для Миши — одна «категория».
6. **HUD-simplify** («растянутость левого блока, слишком умно» — отдельный скоуп под Мишу-нетеха; power-ручки за fold).
7. **hide с фейдом** ease-in-out (LMB-скрытие ноды/панели) — из спеки #9.
8. **hover-pin из кнопки прав.бара** (спавн без 2×rmb).
9. **auto-sync стоимость на масштабе**: regen с детекторами на 2300 = tag/temporal O(n²) медленно. Нужен semantic-only быстрый regen-режим (emb-cache спасает только semantic).
10. **hover-pin наследует дизайн мышь-тултипа**: сейчас createHoverPin = кастомный inline-стиль; мышь-`.tooltip` (tag-чипы цветные, meta, links) красивее. Переписать карточку на ту же HTML/CSS-структуру (grep `-a` `tooltip.innerHTML`, `.ttags`/`.tmeta`), сохранив mdRender-тело+драг+кнопки. Юзер: «ховеры пины не наследуют дизайн ховеров мышкой».
11. **browse right-click context-меню**: `atlasctx` (сейчас только «✎ Редактировать» на contextmenu превью) расширить — pin/＋нота/read/edit. Юзер: «непаханое поле контекстного меню правым в бравсе, одной из кнопок будет пин». Pin из browse = `togglePin` (граф-scope, экспорт в window).

## Правила
- Правки рантайма — python-патчер с `assert s.count(old)==1` + `.bak-*` (потом в scratchpad, НЕ в репо). Читай ПЕРЕД правкой (EDIT-WITHOUT-READ). Self-test после КАЖДОЙ.
- Коммиты typed, БЕЗ `Co-Authored-By`. Не пушить (юзер триггерит).
- Объяснять фичи прозой, не кавеманом. i18n RU-база + EN + UK.
- Юзер тестит живьём через swappy на Арче (`~/Desktop/swappy-*.png`) — тяни `rsync arch:...`. Feel-тюнинг верифицируй ГЛАЗАМИ (свой скрин или его swappy), не клейми «работает» вслепую.
