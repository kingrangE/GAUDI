---
name: frontend-design
description: Build and style frontend UI in the and-you "judge console" design language. Use whenever you create or restyle any screen, page, or component under frontend/ — covers the palette tokens, the shared @/components/ui primitives to reuse, the Tailwind-vs-CSS-Module rule, and do/don'ts. Triggers on "build a screen/page/component", "style this", "add a UI", or any frontend visual work.
---

# frontend-design

Every screen in `and-you` speaks one visual language — minsu's **"judge console"**. Match it; don't
invent a new look. **Reuse the shared primitives before writing markup.** This skill is the canonical
guide; the source of truth in code is `frontend/tailwind.config.ts` + `frontend/src/app/globals.css`.

## The identity (read first)

A disciplined **online-judge workspace**, not a consumer app:

- **Light cool-gray chrome** (`paper`/`surface`) for instructions, forms, metadata —
- **plus exactly ONE dark "ink" code well** (`bg-ink-900`) for code, agent output, or the result the
  user is judging. The dark zone is the single dramatic moment; don't scatter dark surfaces.
- **Restrained indigo accent** (`brand-600`) for the *one* primary action / focus / active state.
- **Monospace carries the identity**: kickers, labels, verdicts, numbers, line numbers use JetBrains
  Mono, 11px, UPPERCASE, wide tracking. This is the signature — use `SectionLabel`/`CodeMeta`, not ad-hoc text.
- Information-dense, tight spacing, soft (not playful) corners. No gradients, no decorative shadows.

## Reuse these primitives — don't re-build them

Import from `@/components/ui/*`. Compose these before hand-rolling markup or colors.

| Primitive | Props / variants | Use for |
|---|---|---|
| `Button` | `variant: "primary" \| "secondary" \| "ghost"` | actions. One `primary` per view. |
| `Badge` | `tone: "neutral" \| "good" \| "bad" \| "brand" \| "warn"` | difficulty, pass/fail, outcomes, %, grades |
| `Panel` | `tone: "light" \| "dark"`, `flush?` | card (`light`=white) or the one code/output well (`dark`) |
| `CodePanel` | `label`, `meta?`, `code?` \| `children?`, `flushBody?` | dark ink panel w/ header (code / agent output) |
| `CodeMeta` | children | small mono tag in a CodePanel header (lang, turn #) |
| `SectionLabel` | `onDark?` | the uppercase mono kicker ("AGENT OUTPUT") |
| `Metric` | `label`, `value`, `hint?` | a score / Precision / big number readout |
| `Chips` | `items: string[]`, `tone: "good" \| "warn"` | keyword chips (strengths / weaknesses) |
| `Tabs` | `tabs`, `active`, `onChange` | tab strip |
| `AppShell` | wraps page | top nav + layout. **Skip it on the `/` entry/gate route** (full-screen). |
| `cn(...)` | — | join conditional class strings (the repo's clsx) |

If you need a new shared primitive, add it under `@/components/ui/` (Tailwind-only, variant via a prop
union) — don't bake one-off colors into a feature component.

## Tokens — use the named token, never a raw hex

Tailwind class names are stable (`brand`/`ink`/`good`/`bad`/`warn`); only their values are minsu's.
**Never** use arbitrary hex (`text-[#...]`, `bg-[#...]`) or off-palette colors.

**Chrome (light):** `paper #eceef3` (page bg) · `surface #ffffff` (cards) · `line #dde1e9` (borders)

**Accent (indigo `brand`):** `600 #3a36c4` (primary action) · `700 #302da6` (hover) · `50 #eef0fb` /
`100 #dcdef6` / `200 #b9bdec` / `300 #9a9ee4` (tints: active tab, focus ring, feature label)

**Ink (the dark well + text):** `900 #14161c` (code bg) · `700 #23262f` (head border) ·
`600 #2a2e38` (dark border) · `text #e6e8ee` (on dark) · `soft #5b6270` (secondary) · `faint #8b91a0` (muted/kickers)

**Verdict (semantic — use the matching `Badge`/`Chips` tone, not the hex):**
`good #1f9d5a` = pass/accept/strength · `bad #d23b3b` = fail/reject/error/weakness · `warn #c08218` = caution/timeout.
Each has `50`/`100` tints for badge backgrounds (e.g. `bg-good-50 text-good-700 border-good-100`).

**Type:** mono = `font-mono` (JetBrains Mono). Kickers: `text-[11px] uppercase tracking-[0.14em] text-ink-faint`.
Body: system sans, 13–14px (`text-sm`). Big numbers/scores: `font-mono text-2xl font-bold tabular-nums`.

**Shape:** radius `rounded-lg` (cards) / `rounded-full` (pills/badges) / `rounded-md` (buttons, chips).
Shadow: only `shadow-panel` on light cards; dark wells get none.

## Tailwind vs CSS Module — the rule

- **Tailwind utilities** for primitives and small/interactive components (the default; see `@/components/ui`).
  Conditional classes via `cn()`.
- **CSS Module** (`feature.module.css`) only for **complex feature layouts** (multi-pane grids, ledgers)
  and feature-scoped dark surfaces. Pull values from the `--paper/--surface/--ink/--accent/--ac/--wa/--mono`
  CSS vars in `globals.css` — don't re-declare new hex.

## Do / Don't

- ✅ Reuse `@/components/ui` primitives and palette tokens. ❌ Don't write raw markup with arbitrary hex.
- ✅ One `brand-600` primary action + one dark `ink` well per view. ❌ Don't multiply accents or dark zones.
- ✅ Use `Badge`/`Chips` semantic tones for pass/fail/caution. ❌ Don't color outcomes by hand.
- ✅ Kickers via `SectionLabel` (mono/upper/tracked). ❌ Don't fake the kicker style inline.
- ✅ Keep feature UI HTTP-only (call the backend). ❌ Never call an LLM from the client.

## Build-a-screen checklist

1. Wrap in `AppShell` (except `/`). Establish light chrome (`bg-paper`, white `Panel`s).
2. Reuse primitives for every element that has one; only then write Tailwind markup.
3. Put code/output/the-thing-being-judged in a single `dark` `Panel`/`CodePanel`.
4. Color only through palette tokens / semantic tones. Grep your diff for `[#` — there should be none.
5. Label sections with `SectionLabel`; show scores with `Metric`.
6. `npm run lint && npm run typecheck && npm test` green before a PR.
