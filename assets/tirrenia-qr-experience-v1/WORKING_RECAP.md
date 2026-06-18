# Tirrenia QR Landing - Working Recap

Date: 2026-06-15
Branch: `pr/qr-experience-v1`
Worktree root: `/home/administrator/env/workspace/itermodus/tirrenia/tirrenia-platform/var/syncwheel/qr-experience-v1`

## Current State

We are building the QR landing page for Tirrenia, based on a golden mobile reference image.
The implementation has moved from a one-file static prototype into the Next.js public site:

- React app: `workspaces/tirrenia-site/`
- Entrypoint: `workspaces/tirrenia-site/src/components/QrExperience.tsx`
- Shared visual CSS: `workspaces/tirrenia-site/public/assets/tirrenia-qr-experience-v1/qr.css`
- Shared header custom element: `workspaces/tirrenia-site/public/assets/tirrenia-header/`

The current implementation is no longer just a scaled poster on mobile:

- Desktop/tablet above `600px` keeps the original poster-style composition and remains close to the `1086 x 1448` golden reference.
- Phones at `600px` and below use a dedicated mobile layout with normal document flow, real text, and reusable extracted visual assets.
- The project is tracked in Git despite living under `var/syncwheel`; this path is a real Git worktree managed by syncwheel.

Main React page:

```text
/home/administrator/env/workspace/itermodus/tirrenia/tirrenia-platform/var/syncwheel/qr-experience-v1/workspaces/tirrenia-site/src/components/QrExperience.tsx
```

Main asset folder:

```text
/home/administrator/env/workspace/itermodus/tirrenia/tirrenia-platform/var/syncwheel/qr-experience-v1/workspaces/tirrenia-site/public/assets/tirrenia-qr-experience-v1/
```

Next dev preview used during work:

```text
http://192.168.3.107:4183/nl_NL/landing/qr/kw42/
```

## Important Commits

Latest relevant commits on `pr/qr-experience-v1`:

```text
d53ebf1 fix(qr): tune mobile typography
bd61da5 feat(qr): add dedicated mobile layout
aeb25b6 fix(qr): refine mobile copy and scale
af6943b fix(qr): clean cta artifacts
c23fae6 fix(qr): soften paper edge seams
f395c13 fix(qr): extend static preview background
d9055f1 fix(qr): refine static page visual assets
3741532 chore(qr): checkpoint static experience baseline
344b40c chore(syncwheel): register qr experience stack
```

Rollback anchors:

- Roll back only the latest mobile typography/copy tweak: `git revert d53ebf1`
- Roll back the dedicated mobile layout experiment: `git revert bd61da5`
- Return to the last scaled-poster mobile approach: `aeb25b6`

Do not use destructive reset unless Joseph explicitly asks.

## Architecture

### Desktop / Golden Layout

The desktop/golden layout is still the original poster composition:

- wrapper: `.qr-stage`
- scaled shell: `.qr-shell`
- artboard: `.qr-artboard`
- breakpoint: visible above `600px`
- React scaling hook: `useQrDesktopScale()` in `workspaces/tirrenia-site/src/components/QrExperience.tsx`

This layout uses the exported Odoo-like header component from:

```text
workspaces/tirrenia-site/public/assets/tirrenia-header/
```

The desktop layer deliberately keeps the `1086 x 1448` coordinate system.
Do not casually refactor this if the task is only mobile tuning.

### Dedicated Mobile Layout

The mobile layout was added because the scaled golden poster was too small on phones and produced a large empty area at the bottom.

Mobile wrapper:

```html
<div class="qr-mobile-stage" data-qr-mobile-stage>
```

It becomes visible under:

```css
@media (max-width: 600px)
```

Mobile uses:

- real mobile header from `<tirrenia-header>`
- real text for all normal copy
- extracted icons/dividers/arrows
- a clean reusable mobile paper asset

Important generated mobile asset:

```text
workspaces/tirrenia-site/public/assets/tirrenia-qr-experience-v1/generated/paper-mobile-card-base.png
```

It is created by:

```text
workspaces/tirrenia-site/public/assets/tirrenia-qr-experience-v1/tools/extract-assets.py
```

The `paper-mobile-card` crop is intentionally a cleaned blank paper card. It avoids the old problem where `paper-feedback-base.png` contained baked CTA/stamp fragments that showed up as ghosts in the mobile card.

## Asset Strategy

The page uses extracted assets from:

```text
workspaces/tirrenia-site/public/assets/tirrenia-qr-experience-v1/source/qr-golden.png
```

Key rules Joseph established:

- Normal readable copy must be HTML text, not raster text.
- The circular `GRAZIE MILLE / PER LA VISITA` stamp may remain graphical.
- On desktop, the stamp is baked into `paper-feedback-base.png`; do not separate it unless there is a very good reason.
- For mobile, the stamp is separate/decorative (`generated/stamp.png`) so it can sit low/right without interfering with text.
- Do not regenerate the visual system from scratch.
- Fixes should be surgical and preserve the current direction unless Joseph explicitly asks for a redesign.

Extractor script:

```text
workspaces/tirrenia-site/public/assets/tirrenia-qr-experience-v1/tools/extract-assets.py
```

Generated assets:

```text
workspaces/tirrenia-site/public/assets/tirrenia-qr-experience-v1/generated/
```

If changing extraction coordinates, regenerate with:

```bash
python3 workspaces/tirrenia-site/public/assets/tirrenia-qr-experience-v1/tools/extract-assets.py
```

Then inspect generated PNGs and page screenshots.

## Current Copy

Hero:

```text
BENVENUTI A TIRRENIA
Napoli spirit. Haarlem home.
A small bar of coffee, warmth,
and familiar rituals — just for you.
Welcome to our banco.
```

Story card:

```text
ABOUT
Our story
From Napoli to Haarlem.
Discover the heart behind
Tirrenia.
```

Menu card:

```text
MENU
Our delicacies
Coffee, dolci, sweet and
savory specials.
See what Tirrenia has to offer.
```

Feedback card:

```text
ANONYMOUS FEEDBACK
Help to improve
Tell us how it felt.
Your visit helps keep the
ritual alive.
```

CTA:

```text
ORDER AT THE BAR
Grazie!
```

Note: `ORDER AT THE BAR` intentionally has no trailing period.

## Mobile Typography Status

Latest request implemented in `d53ebf1`:

- Hero mobile text made smaller.
- Mobile card titles made about 20% smaller.
- Feedback label changed to `ANONYMOUS FEEDBACK`.
- Feedback title changed to `Help to improve`.

Relevant CSS selectors:

```text
.mobile-kicker
.mobile-hero h1
.mobile-hero p:last-child
.mobile-title
.mobile-feedback .mobile-title
```

Current mobile layout was visually checked at:

- `412 x 915` S23-like
- `390 x 844`
- `360 x 800`
- `430 x 932`
- desktop `1086 x 1448`

Observed state after latest change:

- S23-like layout fits the viewport without the old huge bottom void.
- `390px` and `360px` may have a short scroll; that is accepted because readability is better than forcing the poster to shrink.
- Desktop still uses `.qr-stage`, not the mobile layout.

## Known Issues / Watch Points

1. `tools/__pycache__/` is untracked.
   - It is harmless and should not be committed.
   - It can be ignored or removed if desired, but it was left untouched.

2. `syncwheel check` exits `0` but warns:

```text
WARN: integration contains 31 non-merge commit(s) not declared in any stack
```

This warning predates the QR work. Do not fix it as part of QR visual tuning unless Joseph explicitly asks.

3. The desktop/golden version is no longer the source of truth for phone UX.
   - Phone UX is now the dedicated mobile layout.
   - Do not judge mobile readability by the `1086` poster scaling anymore.

4. The mobile layout uses the same aesthetic, not exact 1:1 golden positioning.
   - This was a deliberate solution to make the QR page usable on real phones.

5. If text is adjusted, verify both mobile and desktop:
   - Desktop copy can still overflow because desktop card coordinates are fixed.
   - Mobile text can collide with arrows/stamp if labels get longer.

## Recommended QA Commands

Start/confirm Next preview:

```bash
cd workspaces/tirrenia-site
bun install
bun run dev:nestdev
```

Open:

```text
http://192.168.3.107:4183/nl_NL/landing/qr/kw42/
```

Manual screenshot targets:

- `1086 x 1448`
- `412 x 915`
- `390 x 844`
- `360 x 800`
- `430 x 932`

Minimum checks:

- Desktop still shows poster layout and no duplicated CTA lines.
- Mobile uses the hamburger/header layout, not the desktop social header.
- Mobile hero is readable and not oversized.
- Card titles do not overlap arrows.
- Feedback stamp does not cover text.
- CTA bell is not clipped.
- No ghost text or duplicate CTA fragments inside cards.

## Git / Commit Policy Used

Before and after commits on `pr/qr-experience-v1`, `syncwheel check --manifest .syncwheel/manifest.json` was run.
It consistently reported the known warning about 31 unmapped integration commits but exited successfully.

Recent work was pushed to:

```text
origin/pr/qr-experience-v1
```

Current latest commit:

```text
d53ebf1 fix(qr): tune mobile typography
```

## Practical Continuation Notes

If continuing work:

1. Work in this worktree:

```text
/home/administrator/env/workspace/itermodus/tirrenia/tirrenia-platform/var/syncwheel/qr-experience-v1
```

2. Keep edits scoped to:

```text
workspaces/tirrenia-site/public/assets/tirrenia-qr-experience-v1/qr.css
workspaces/tirrenia-site/public/assets/tirrenia-qr-experience-v1/tools/extract-assets.py
workspaces/tirrenia-site/public/assets/tirrenia-qr-experience-v1/generated/
workspaces/tirrenia-site/
```

3. Prefer CSS/HTML copy tweaks before changing extraction.

4. If visual assets are changed, update the extractor script and regenerate rather than hand-editing PNGs manually.

5. Keep the mobile layout as the phone UX unless Joseph asks to revert it.

6. If Joseph says "rollback solution 3", revert `bd61da5` and any later commits that depend on it, or branch from `aeb25b6`.
