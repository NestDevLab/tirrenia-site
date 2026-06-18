# QR Page 1:1 Rescue Brief

Source coordinate system: `1086 x 1448` pixels.

## Locked Baseline - 2026-06-14

This implementation is now the protected baseline for the Tirrenia QR page.
Do not restart from scratch, redesign the page, regenerate the whole visual
system, or replace the current composition with a different strategy.

Future work must be surgical and incremental:

- Commit this baseline before any further visual corrections.
- Preserve the current layered-asset composition.
- Fix many small issues in place rather than rebuilding the page.
- Keep all normal visible copy as real HTML text, not raster text baked into
  image assets.
- Use Tirrenia Concept fonts where practical, or a close equivalent when needed
  for visual fit. Pixel-identical font matching to the reference image is not
  required; similar style, hierarchy, color, and weight are required.
- The only normal-copy exception is the circular `GRAZIE MILLE / PER LA VISITA`
  stamp, which may remain an extracted image because its circular lettering and
  stamp texture are complex.
- Logos, icons, illustrations, arrows, paper pieces, dividers, shadows, and the
  stamp may remain image assets, but plain labels, headings, paragraphs, and the
  bottom order text must be real HTML text.
- Check and correct clipped/cropped visual assets one by one: cup, cannolo,
  feedback pen/speech bubble, arrows, bell, lines, and any paper edges.
- Fix paper shadows in place, especially the right-side and lower-right shadow
  artifacts where rectangular or dirty background blocks are visible.
- Header and background should eventually fill the full screen, but that is a
  later phase. First stabilize the mobile reference composition.
- Desktop landing adaptation is a final phase after the mobile baseline is
  visually stable.
- Subagents may work on this, but only with narrow ownership and explicit
  micro-fix briefs. They must not reinterpret the plan or propose a wholesale
  rebuild.

## Strategy

- Use the exported real Odoo-like header from `workspaces/tirrenia-site/public/assets/tirrenia-header/`; do not replace it with a screenshot.
- Keep normal visible copy as real HTML text using Tirrenia Concept fonts.
- Keep the circular `GRAZIE MILLE / PER LA VISITA` stamp baked into `paper-feedback-base.png` through the preserved foreground region.
- Keep `paper-*-shadow.png` and `paper-*-edge.png` for layer compatibility; the current wide-plate pass carries the visible paper, local background, and natural baked shadow in `paper-*-base.png`.
- Use `paper-mobile-card-base.png` only for the dedicated mobile layout; it is a blank paper strip with icons/text/arrow removed so mobile can compose separate real text and cutout assets.
- Start `paper-*-base.png` from the real golden crop, then cover only fixed text/line/icon cleanup regions with source-sampled paper texture through irregular feathered masks.
- Extract arrows with a blue-ink mask so the circular arrow mark remains intact.

## Layering

Within each card/order layer:

1. compatibility `paper-*-shadow.png`
2. `paper-*-base.png` with paper, baked icons/dividers/stamp, and local background
3. compatibility `paper-*-edge.png`
4. extracted arrows/lines/bell where needed
5. real HTML text

## Cleanup Rectangles

Rectangles are `x0,y0,x1,y1`, relative to each paper crop.

```text
paper-story:
  copy    390,51,790,270
  arrow   770,135,905,275
paper-menu:
  copy    390,41,820,238
  arrow   770,96,905,240
paper-feedback:
  copy    390,50,800,252
  arrow   770,105,905,250
  line    0,360,270,390
  line    710,360,1000,390
paper-order:
  bell    58,38,156,122
  copy    155,24,489,126
  line    0,58,28,92
  line    495,58,523,92
paper-mobile-card:
  icon    70,60,310,260
  divider 330,35,370,285
  copy    360,45,810,285
  arrow   760,120,930,290
```

## Asset Map

Cutouts are extracted from `source/qr-golden.png`; paper bases use wide source crops, preserved non-text visuals, and local sampled paper patches. Shadow/edge PNGs are compatibility layers in this pass.

| Asset | x | y | w | h |
| --- | ---: | ---: | ---: | ---: |
| `body-background` | 0 | 142 | 1086 | 1306 |
| `paper-story` | 54 | 430 | 984 | 348 |
| `paper-menu` | 54 | 728 | 996 | 336 |
| `paper-feedback` | 54 | 996 | 1032 | 390 |
| `paper-order` | 280 | 1302 | 523 | 146 |
| `paper-mobile-card` | 54 | 430 | 984 | 348 |
| `icon-cup` | 150 | 514 | 202 | 177 |
| `icon-cannolo` | 135 | 810 | 235 | 142 |
| `icon-feedback` | 165 | 1083 | 186 | 156 |
| `arrow-story` | 845 | 573 | 86 | 86 |
| `arrow-menu` | 845 | 846 | 86 | 86 |
| `arrow-feedback` | 844 | 1123 | 86 | 94 |
| `divider-story` | 403 | 480 | 16 | 224 |
| `divider-menu` | 403 | 778 | 16 | 205 |
| `divider-feedback` | 403 | 1048 | 16 | 210 |
| `stamp` | 884 | 1188 | 164 | 168 |
| `bell` | 350 | 1354 | 70 | 52 |
| `line-left` | 78 | 1375 | 214 | 10 |
| `line-right` | 793 | 1375 | 198 | 10 |

Generated paper layer sizes:

| Prefix | Base/edge size | Shadow size | Shadow inset |
| --- | ---: | ---: | ---: |
| `paper-story` | `984 x 348` | `1144 x 508` | `-80px` |
| `paper-menu` | `996 x 336` | `1156 x 496` | `-80px` |
| `paper-feedback` | `1032 x 390` | `1192 x 550` | `-80px` |
| `paper-order` | `523 x 146` | `683 x 306` | `-80px` |
| `paper-mobile-card` | `984 x 348` | `1144 x 508` | `-80px` |
