# 0009 – Rule filters

Stage: Archive · Phase 2

## Why

The point of the app is to cut noise. WP in particular mixes real news with teasers
("Jest nagranie", "Ostra reakcja", "Tak oceniają to politycy"), view-count bait
("Aż 1,5 mln wyświetleń") and roundups ("[SKRÓT DNIA]"). Every decision must carry a reason.

## What

- `filters.toml` (user-editable):
  - `muted = []`: words/stems to hide completely (title or text). Empty by default; the
    user named no topics. Same matching as elsewhere: 4+ letters match word starts,
    shorter must be a whole word.
  - `[[rule]]` entries: `lang` (`en`/`pl`/`any`), `pattern` (case-insensitive regex on the
    title), `action` (`drop` = hide, `downrank` = keep but rank lower), `reason`.
- Starting rules, tuned on the real headlines:
  - drop: view-count bait, "nie uwierzysz", "szok", "hit internetu", "internauci oszaleli",
    "you won't believe", "goes viral", "what happens next", "jaw-dropping"
  - downrank: "[SKRÓT DNIA]" roundups, "Jest nagranie/reakcja/żądanie", "Ostra reakcja",
    sentence-initial "Tak …"/"Oto …" teasers, "zobacz/sprawdź", "wiemy, co";
    BBC "Watch:" videos, "Launch HN:" (YC launch ads), listicles, "here's why"
- `article_verdict` table (migration 4): article_id, action (`drop`/`downrank`), reason.
  Recomputed for all articles every run, so editing `filters.toml` applies retroactively.
  Articles without a row are kept normally.
- Story-level effect (used by scoring, 0010): a story is hidden only if all its articles
  are dropped; a dropped article inside a kept story is just not shown.
- `news fetch` summary gains `, N filtered`; invalid regex / action → clear error.

## Acceptance criteria

- On the real headlines: "Aż 1,5 mln wyświetleń…" dropped; "[SKRÓT DNIA]", "Jest nagranie",
  "Ostra reakcja", "Tak oceniają/werbują", "Watch:", "Launch HN:" downranked;
  plain news ("Wypadek śmigłowca EUFOR…", "Russian drone attack…") untouched
- A muted word hides matching articles with reason `muted: <word>`
- pytest + ruff pass

## Approval

User approved the rest of Phase 2 and Phase 3 without further questions (2026-10-29).
No muted topics given: list starts empty.
