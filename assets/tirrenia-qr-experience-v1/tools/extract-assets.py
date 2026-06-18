from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "qr-golden.png"
OUT = ROOT / "generated"


@dataclass(frozen=True)
class Box:
    name: str
    xywh: tuple[int, int, int, int]

    @property
    def xyxy(self) -> tuple[int, int, int, int]:
        x, y, w, h = self.xywh
        return (x, y, x + w, y + h)


BACKGROUND = Box("body-background", (0, 142, 1086, 1306))

BODY_TEXTURE_SAMPLES = [
    (0, 168, 206, 442),
    (880, 168, 1086, 442),
]

PAPER_STRIPS = [
    Box("paper-story", (54, 430, 984, 348)),
    Box("paper-menu", (54, 728, 996, 336)),
    Box("paper-feedback", (54, 996, 1032, 390)),
    Box("paper-order", (280, 1302, 523, 146)),
    Box("paper-mobile-card", (54, 430, 984, 348)),
]

SHADOW_PAD = 80
CLEANUP_EXPAND = 18
PLATE_EDGE_FADE = 42

# Fixed cleanup zones are xyxy rectangles relative to the strip crop.
CLEANUP_RECTS = {
    "paper-story": [
        ("copy", (390, 51, 790, 270)),
        ("arrow", (770, 135, 905, 275)),
    ],
    "paper-menu": [
        ("copy", (390, 41, 820, 238)),
        ("arrow", (770, 96, 905, 240)),
    ],
    "paper-feedback": [
        ("copy", (390, 50, 800, 252)),
        ("arrow", (770, 105, 905, 250)),
        ("line", (0, 360, 270, 390)),
        ("line", (710, 360, 1000, 390)),
    ],
    "paper-order": [
        ("bell", (58, 38, 156, 122)),
        ("copy", (155, 24, 489, 126)),
        ("line", (0, 58, 28, 92)),
        ("line", (495, 58, 523, 92)),
    ],
    "paper-mobile-card": [
        ("icon", (70, 60, 310, 260)),
        ("divider", (330, 35, 370, 285)),
        ("copy", (360, 45, 810, 285)),
        ("arrow", (760, 120, 930, 290)),
    ],
}

PRESERVE_RECTS = {
    "paper-feedback": [
        ("stamp", (800, 165, 1032, 382)),
    ],
}

CUTOUTS = [
    Box("icon-cup", (150, 514, 202, 177)),
    Box("icon-cannolo", (135, 810, 235, 142)),
    Box("icon-feedback", (165, 1083, 186, 156)),
    Box("arrow-story", (845, 573, 86, 86)),
    Box("arrow-menu", (845, 846, 86, 86)),
    Box("arrow-feedback", (844, 1123, 86, 94)),
    Box("divider-story", (403, 480, 16, 224)),
    Box("divider-menu", (403, 778, 16, 205)),
    Box("divider-feedback", (403, 1048, 16, 210)),
    Box("stamp", (884, 1188, 164, 168)),
    Box("bell", (350, 1354, 70, 52)),
    Box("line-left", (78, 1375, 214, 10)),
    Box("line-right", (793, 1375, 198, 10)),
]

CUTOUT_PADDING = {
    "icon-cup": 6,
    "icon-cannolo": 6,
    "icon-feedback": 6,
    "arrow-story": 8,
    "arrow-menu": 8,
    "arrow-feedback": 8,
    "bell": 6,
}

LOCKED_BASELINE_FALLBACK = [
    "## Locked Baseline - 2026-06-14",
    "",
    "This implementation is now the protected baseline for the Tirrenia QR page.",
    "Do not restart from scratch, redesign the page, regenerate the whole visual",
    "system, or replace the current composition with a different strategy.",
    "",
    "Future work must be surgical and incremental:",
    "",
    "- Commit this baseline before any further visual corrections.",
    "- Preserve the current layered-asset composition.",
    "- Fix many small issues in place rather than rebuilding the page.",
    "- Keep all normal visible copy as real HTML text, not raster text baked into",
    "  image assets.",
    "- Use Tirrenia Concept fonts where practical, or a close equivalent when needed",
    "  for visual fit. Pixel-identical font matching to the reference image is not",
    "  required; similar style, hierarchy, color, and weight are required.",
    "- The only normal-copy exception is the circular `GRAZIE MILLE / PER LA VISITA`",
    "  stamp, which must remain baked inside `paper-feedback-base.png`; do not",
    "  render it as a separate overlay during this rescue pass.",
    "- Logos, icons, illustrations, arrows, paper pieces, dividers, shadows, and the",
    "  stamp may remain image assets, but plain labels, headings, paragraphs, and the",
    "  bottom order text must be real HTML text.",
    "- Check and correct clipped/cropped visual assets one by one: cup, cannolo,",
    "  feedback pen/speech bubble, arrows, bell, lines, and any paper edges.",
    "- Fix paper shadows in place, especially the right-side and lower-right shadow",
    "  artifacts where rectangular or dirty background blocks are visible.",
    "- Header and background should eventually fill the full screen, but that is a",
    "  later phase. First stabilize the mobile reference composition.",
    "- Desktop landing adaptation is a final phase after the mobile baseline is",
    "  visually stable.",
    "- Subagents may work on this, but only with narrow ownership and explicit",
    "  micro-fix briefs. They must not reinterpret the plan or propose a wholesale",
    "  rebuild.",
]


def padded_xyxy(box: Box, source_size: tuple[int, int]) -> tuple[int, int, int, int]:
    padding = CUTOUT_PADDING.get(box.name, 0)
    x, y, width, height = box.xywh
    source_width, source_height = source_size
    return (
        max(0, x - padding),
        max(0, y - padding),
        min(source_width, x + width + padding),
        min(source_height, y + height + padding),
    )


def blue_ink_array(crop: Image.Image) -> np.ndarray:
    rgba = crop.convert("RGBA")
    arr = np.asarray(rgba).astype(np.int16)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3] > 0
    r = rgb[:, :, 0]
    g = rgb[:, :, 1]
    b = rgb[:, :, 2]
    maximum = rgb.max(axis=2)
    minimum = rgb.min(axis=2)
    chroma = maximum - minimum
    lum = (0.299 * r) + (0.587 * g) + (0.114 * b)
    return (
        (b > r + 14)
        & (b > g - 16)
        & (b > 54)
        & (r < 182)
        & (lum < 214)
        & ((b - r > 22) | (g - r > 10) | (chroma > 34))
        & alpha
    )


def foreground_array(crop: Image.Image) -> np.ndarray:
    rgba = crop.convert("RGBA")
    arr = np.asarray(rgba).astype(np.int16)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3] > 0
    r = rgb[:, :, 0]
    g = rgb[:, :, 1]
    b = rgb[:, :, 2]
    maximum = rgb.max(axis=2)
    minimum = rgb.min(axis=2)
    chroma = maximum - minimum
    lum = (0.299 * r) + (0.587 * g) + (0.114 * b)
    lum_image = Image.fromarray(np.clip(lum, 0, 255).astype(np.uint8), "L")
    local_lum = np.asarray(lum_image.filter(ImageFilter.GaussianBlur(4.0))).astype(np.float32)
    local_delta = local_lum - lum

    blue_ink = blue_ink_array(crop)
    dark_ink = (lum < 150) & (r < 174) & (g < 164) & (b < 158) & (local_delta > 8)
    brown_type = (lum < 158) & (r >= g - 8) & (g >= b - 20) & (local_delta > 9)
    grey_ink = (lum < 192) & (chroma < 44) & (local_delta > 5)
    faint_grey_ink = (lum < 218) & (chroma < 38) & (local_delta > 9)

    return (blue_ink | dark_ink | brown_type | grey_ink | faint_grey_ink) & alpha


def foreground_mask(crop: Image.Image, dilation: int = 3, blur: float = 0.65) -> Image.Image:
    mask = Image.fromarray(foreground_array(crop).astype(np.uint8) * 255, "L")
    if dilation > 1:
        mask = mask.filter(ImageFilter.MaxFilter(dilation))
    if blur > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    return mask


def blue_ink_mask(crop: Image.Image, dilation: int = 3, blur: float = 0.65) -> Image.Image:
    mask = Image.fromarray(blue_ink_array(crop).astype(np.uint8) * 255, "L")
    if dilation > 1:
        mask = mask.filter(ImageFilter.MaxFilter(dilation))
    if blur > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    return mask


def save_cutout(source: Image.Image, box: Box) -> None:
    crop = source.crop(padded_xyxy(box, source.size)).convert("RGBA")
    if box.name.startswith("line-"):
        arr = np.asarray(crop.convert("RGB")).astype(np.uint8)
        rgb = arr.astype(np.int16)
        r = rgb[:, :, 0]
        g = rgb[:, :, 1]
        b = rgb[:, :, 2]
        lum = (0.299 * r) + (0.587 * g) + (0.114 * b)
        blue = (b > r + 28) & (b > g - 8) & (r < 120) & (g < 165) & (b < 200) & (lum < 155)
        mask = Image.fromarray(blue.astype(np.uint8) * 255, "L").filter(ImageFilter.GaussianBlur(0.35))
        pixels = arr[blue]
        color = np.median(pixels, axis=0).astype(np.uint8) if pixels.size else np.array([24, 95, 140], dtype=np.uint8)
        rgba = np.zeros((crop.height, crop.width, 4), dtype=np.uint8)
        rgba[:, :, :3] = color
        rgba[:, :, 3] = np.asarray(mask)
        Image.fromarray(rgba, "RGBA").save(OUT / f"{box.name}.png")
        return
    if box.name.startswith("arrow-"):
        mask = blue_ink_mask(crop, dilation=3, blur=0.65)
    else:
        mask = foreground_mask(crop)
    crop.putalpha(mask)
    crop.save(OUT / f"{box.name}.png")


def noise_field(width: int, height: int, seed: int, radius: float, scale: float) -> np.ndarray:
    rng = np.random.default_rng(seed)
    raw = rng.normal(128, 32, (height, width)).clip(0, 255).astype(np.uint8)
    blurred = Image.fromarray(raw, "L").filter(ImageFilter.GaussianBlur(radius))
    arr = np.asarray(blurred).astype(np.float32)
    arr -= float(arr.mean())
    std = float(arr.std()) or 1.0
    return (arr / std) * scale


def add_texture_noise(image: Image.Image, seed: int, low_scale: float, fine_scale: float) -> Image.Image:
    rgb = image.convert("RGB")
    width, height = rgb.size
    arr = np.asarray(rgb).astype(np.float32)
    low = noise_field(width, height, seed, 17.0, low_scale)
    fine = noise_field(width, height, seed + 101, 0.8, fine_scale)
    yy, xx = np.mgrid[0:height, 0:width]
    fibre = (((xx * 13 + yy * 29 + seed * 7) % 17) - 8).astype(np.float32) * 0.16
    shade = low + fine + fibre
    arr += shade[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def stitch_samples(source: Image.Image, boxes: list[tuple[int, int, int, int]]) -> Image.Image:
    samples = [source.crop(box).convert("RGB") for box in boxes]
    height = min(sample.height for sample in samples)
    width = sum(sample.width for sample in samples)
    out = Image.new("RGB", (width, height))
    left = 0
    for sample in samples:
        sample = sample.crop((0, 0, sample.width, height))
        out.paste(sample, (left, 0))
        left += sample.width
    return out


def clean_pixel_pool(crop: Image.Image, paper_mask: Image.Image | None = None) -> np.ndarray:
    rgba = crop.convert("RGBA")
    rgb = np.asarray(rgba)[:, :, :3].astype(np.uint8)
    foreground = np.asarray(
        foreground_mask(rgba, dilation=9, blur=0),
    ) > 0
    light_paper = (
        (rgb[:, :, 0] > 198)
        & (rgb[:, :, 1] > 188)
        & (rgb[:, :, 2] > 172)
        & (rgb[:, :, 0] - rgb[:, :, 2] < 38)
    )
    if paper_mask is not None:
        light_paper &= np.asarray(paper_mask.resize(rgba.size, Image.Resampling.BICUBIC)) > 170
    clean = light_paper & ~foreground
    pixels = rgb[clean]
    if pixels.size < 100:
        pixels = rgb[light_paper]
    if pixels.size < 100:
        pixels = rgb.reshape((-1, 3))
    return pixels.astype(np.float32)


def paper_texture_from_pixels(
    pixels: np.ndarray,
    size: tuple[int, int],
    seed: int,
) -> Image.Image:
    color = np.median(pixels, axis=0)
    spread = np.clip(np.std(pixels, axis=0), 1.5, 5.5)
    width, height = size
    yy, xx = np.mgrid[0:height, 0:width]
    fibre = (((xx * 11 + yy * 23 + seed * 5) % 19) - 9).astype(np.float32) * 0.22
    low = noise_field(width, height, seed, 8.0, 2.2)
    fine = noise_field(width, height, seed + 211, 0.55, 1.15)
    arr = np.zeros((height, width, 3), dtype=np.float32)
    for channel in range(3):
        arr[:, :, channel] = color[channel] + (low * 0.8) + fine + fibre
        arr[:, :, channel] += noise_field(width, height, seed + 37 + channel, 2.0, float(spread[channel]) * 0.18)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").filter(
        ImageFilter.GaussianBlur(0.18),
    )


def paper_texture(
    crop: Image.Image,
    size: tuple[int, int],
    seed: int,
    paper_mask: Image.Image | None = None,
) -> Image.Image:
    return paper_texture_from_pixels(clean_pixel_pool(crop, paper_mask=paper_mask), size, seed)


def odd_filter_size(value: int) -> int:
    return max(3, value if value % 2 else value + 1)


def background_reference(crop: Image.Image) -> np.ndarray:
    rgb = np.asarray(crop.convert("RGB")).astype(np.float32)
    height, width = rgb.shape[:2]
    margin = max(8, min(width, height) // 9)
    corners = np.concatenate(
        [
            rgb[:margin, :margin].reshape(-1, 3),
            rgb[:margin, -margin:].reshape(-1, 3),
            rgb[-margin:, :margin].reshape(-1, 3),
            rgb[-margin:, -margin:].reshape(-1, 3),
        ],
    )
    bright = corners[corners.mean(axis=1) > 216]
    return np.median(bright if len(bright) > 50 else corners, axis=0)


def raw_paper_seed_mask(crop: Image.Image) -> np.ndarray:
    rgb = np.asarray(crop.convert("RGB")).astype(np.float32)
    reference = background_reference(crop)
    r = rgb[:, :, 0]
    g = rgb[:, :, 1]
    b = rgb[:, :, 2]
    lum = (0.299 * r) + (0.587 * g) + (0.114 * b)
    reference_lum = float((0.299 * reference[0]) + (0.587 * reference[1]) + (0.114 * reference[2]))
    color_distance = np.sqrt(((rgb - reference) ** 2).sum(axis=2))
    shadow = lum < reference_lum - 12.0
    contrast = color_distance > 22.0
    foreground = foreground_array(crop)
    raw = (contrast | shadow) & ~foreground
    raw_image = Image.fromarray(raw.astype(np.uint8) * 255, "L")
    raw_image = raw_image.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.1))
    return np.asarray(raw_image) > 18


def fill_holes(mask: np.ndarray) -> np.ndarray:
    height, width = mask.shape
    exterior = np.zeros_like(mask, dtype=bool)
    queue: deque[tuple[int, int]] = deque()
    for x in range(width):
        for y in (0, height - 1):
            if not mask[y, x] and not exterior[y, x]:
                exterior[y, x] = True
                queue.append((x, y))
    for y in range(height):
        for x in (0, width - 1):
            if not mask[y, x] and not exterior[y, x]:
                exterior[y, x] = True
                queue.append((x, y))

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < width and 0 <= ny < height and not mask[ny, nx] and not exterior[ny, nx]:
                exterior[ny, nx] = True
                queue.append((nx, ny))
    return mask | ~exterior


def strip_silhouette(crop: Image.Image) -> np.ndarray:
    raw = raw_paper_seed_mask(crop)
    height, width = raw.shape
    filled = np.zeros_like(raw, dtype=bool)
    min_pixels = max(8, width // 35)
    min_span = max(24, width // 5)

    for y in range(height):
        xs = np.where(raw[y])[0]
        if len(xs) < min_pixels:
            continue
        x0 = int(np.percentile(xs, 1))
        x1 = int(np.percentile(xs, 99))
        if x1 - x0 >= min_span:
            filled[y, x0 : x1 + 1] = True

    filled_image = Image.fromarray(filled.astype(np.uint8) * 255, "L")
    filled_image = filled_image.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(5))
    filled = np.asarray(filled_image) > 0
    return largest_component(fill_holes(filled | raw))


def cleanup_edge_removal_mask(
    size: tuple[int, int],
    rects: list[tuple[str, tuple[int, int, int, int]]],
) -> Image.Image:
    width, height = size
    mask = Image.new("L", size, 0)
    for label, rect in rects:
        x0, y0, x1, y1 = expand_rect(rect, 8, size)
        if x1 > x0 and y1 > y0:
            mask.paste(255, (x0, y0, x1, y1))
        if label == "arrow":
            lower = clamp_rect((x0 - 40, y1 - 6, width, height), size)
            side = clamp_rect((x1 - 8, y0 - 14, width, min(height, y1 + 28)), size)
            for extra in (lower, side):
                ex0, ey0, ex1, ey1 = extra
                if ex1 > ex0 and ey1 > ey0:
                    mask.paste(255, extra)
    return mask.filter(ImageFilter.GaussianBlur(1.4))


def perimeter_overlay_mask(alpha: Image.Image, foreground: Image.Image, cleanup: Image.Image) -> Image.Image:
    width, height = alpha.size
    band = 10 if height <= 120 else 18
    eroded = alpha.filter(ImageFilter.MinFilter(odd_filter_size((band * 2) + 1)))
    alpha_arr = np.asarray(alpha).astype(np.float32) / 255.0
    eroded_arr = np.asarray(eroded).astype(np.float32) / 255.0
    band_arr = np.clip((alpha_arr - eroded_arr) * 1.9, 0.0, 1.0)
    foreground_arr = np.asarray(foreground).astype(np.float32) / 255.0
    cleanup_arr = np.asarray(cleanup).astype(np.float32) / 255.0
    removal_arr = np.maximum(np.clip(foreground_arr * 1.2, 0.0, 1.0), cleanup_arr)
    band_arr *= 1.0 - np.clip(removal_arr, 0.0, 1.0)
    band_mask = Image.fromarray(np.clip(band_arr * 255, 0, 255).astype(np.uint8), "L")
    return band_mask.filter(ImageFilter.GaussianBlur(1.4))


def largest_component(mask: np.ndarray) -> np.ndarray:
    height, width = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    best: list[tuple[int, int]] = []
    for start_y in range(height):
        for start_x in range(width):
            if visited[start_y, start_x] or not mask[start_y, start_x]:
                continue
            queue: deque[tuple[int, int]] = deque([(start_x, start_y)])
            visited[start_y, start_x] = True
            component: list[tuple[int, int]] = []
            while queue:
                x, y = queue.popleft()
                component.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < width and 0 <= ny < height and mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        queue.append((nx, ny))
            if len(component) > len(best):
                best = component

    out = np.zeros_like(mask, dtype=bool)
    for x, y in best:
        out[y, x] = True
    return out


def paper_alpha_mask(crop: Image.Image) -> Image.Image:
    hard = strip_silhouette(crop)
    hard_image = Image.fromarray(hard.astype(np.uint8) * 255, "L")
    softened = hard_image.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.6))
    solid = hard_image.filter(ImageFilter.MinFilter(3))
    alpha = np.maximum(np.asarray(softened), np.asarray(solid))
    return Image.fromarray(alpha.astype(np.uint8), "L")


def plate_alpha_mask(size: tuple[int, int]) -> Image.Image:
    width, height = size
    yy, xx = np.mgrid[0:height, 0:width]
    distance = np.minimum.reduce([xx, yy, width - 1 - xx, height - 1 - yy]).astype(np.float32)
    alpha = np.clip(distance / float(PLATE_EDGE_FADE), 0.0, 1.0) ** 0.85
    return Image.fromarray(np.clip(alpha * 255, 0, 255).astype(np.uint8), "L").filter(
        ImageFilter.GaussianBlur(1.2),
    )


def clamp_rect(rect: tuple[int, int, int, int], size: tuple[int, int]) -> tuple[int, int, int, int]:
    width, height = size
    x0, y0, x1, y1 = rect
    return (max(0, x0), max(0, y0), min(width, x1), min(height, y1))


def expand_rect(rect: tuple[int, int, int, int], amount: int, size: tuple[int, int]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return clamp_rect((x0 - amount, y0 - amount, x1 + amount, y1 + amount), size)


def cleanup_rect_mask(size: tuple[int, int], rects: list[tuple[str, tuple[int, int, int, int]]]) -> Image.Image:
    mask = Image.new("L", size, 0)
    for _, rect in rects:
        x0, y0, x1, y1 = clamp_rect(rect, size)
        if x1 > x0 and y1 > y0:
            mask.paste(255, (x0, y0, x1, y1))
    return mask


def paste_mask(base: Image.Image, mask: Image.Image, xy: tuple[int, int]) -> Image.Image:
    layer = Image.new("L", base.size, 0)
    layer.paste(mask, xy)
    return ImageChops.lighter(base, layer)


def cleanup_edge_guard(size: tuple[int, int]) -> Image.Image:
    width, height = size
    guard = Image.new("L", size, 255)
    if height <= 120:
        return guard
    vertical = 26
    horizontal = 14
    guard.paste(0, (0, 0, width, vertical))
    guard.paste(0, (0, height - vertical, width, height))
    guard.paste(0, (0, 0, horizontal, height))
    guard.paste(0, (width - horizontal, 0, width, height))
    return guard.filter(ImageFilter.GaussianBlur(5.0))


def irregular_patch_mask(mask: Image.Image, seed: int) -> Image.Image:
    hard = mask.filter(ImageFilter.MaxFilter(15))
    expanded = hard.filter(ImageFilter.MaxFilter(23))
    soft = expanded.filter(ImageFilter.GaussianBlur(8.5))
    arr = np.asarray(soft).astype(np.float32)
    noise = noise_field(soft.width, soft.height, seed, 4.0, 1.0)
    jitter = np.clip(0.92 + (noise / 7.5), 0.74, 1.12)
    arr *= jitter
    arr = np.maximum(arr, np.asarray(hard).astype(np.float32))
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "L")


def cleanup_foreground_mask(crop: Image.Image, label: str, rect: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = clamp_rect(rect, crop.size)
    region = crop.crop((x0, y0, x1, y1))
    if label == "copy":
        rgb = np.asarray(region.convert("RGB")).astype(np.float32)
        lum = (0.299 * rgb[:, :, 0]) + (0.587 * rgb[:, :, 1]) + (0.114 * rgb[:, :, 2])
        stroke = lum < 176.0
        stroke_image = Image.fromarray(stroke.astype(np.uint8) * 255, "L")
        return stroke_image.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(1.2))
    if label in {"arrow", "line", "bell"}:
        return blue_ink_mask(region, dilation=11, blur=0.25)
    return foreground_mask(region, dilation=13, blur=0.25)


def local_clean_pixels(
    crop: Image.Image,
    alpha: Image.Image,
    forbidden: Image.Image,
    rect: tuple[int, int, int, int],
) -> np.ndarray:
    rgb = np.asarray(crop.convert("RGB")).astype(np.uint8)
    alpha_arr = np.asarray(alpha) > 178
    forbidden_arr = np.asarray(forbidden) > 0
    foreground_arr = np.asarray(foreground_mask(crop, dilation=13, blur=0)) > 0
    valid = alpha_arr & ~forbidden_arr & ~foreground_arr

    width, height = crop.size
    x0, y0, x1, y1 = clamp_rect(rect, crop.size)
    margin = max(80, min(width, height) // 2)
    local = np.zeros((height, width), dtype=bool)
    local[max(0, y0 - margin) : min(height, y1 + margin), max(0, x0 - margin) : min(width, x1 + margin)] = True
    pixels = rgb[valid & local]
    if pixels.size < 300:
        pixels = rgb[valid]
    if pixels.size < 300:
        pixels = clean_pixel_pool(crop, paper_mask=alpha).astype(np.uint8)
    return pixels.astype(np.float32)


def reconstruct_paper_base(
    crop: Image.Image,
    alpha: Image.Image,
    rects: list[tuple[str, tuple[int, int, int, int]]],
    seed: int,
) -> tuple[Image.Image, Image.Image]:
    base = crop.convert("RGB")
    forbidden = cleanup_rect_mask(crop.size, rects)
    removal = Image.new("L", crop.size, 0)
    edge_guard = cleanup_edge_guard(crop.size)

    for index, (label, rect) in enumerate(rects):
        x0, y0, x1, y1 = expand_rect(rect, CLEANUP_EXPAND, crop.size)
        if x1 <= x0 or y1 <= y0:
            continue
        foreground = cleanup_foreground_mask(crop, label, (x0, y0, x1, y1))
        if np.asarray(foreground).max() == 0:
            continue
        soft = irregular_patch_mask(foreground, seed + (index * 53))
        soft_full = Image.new("L", crop.size, 0)
        soft_full.paste(soft, (x0, y0))
        soft_full = ImageChops.multiply(soft_full, edge_guard)
        pixels = local_clean_pixels(crop, alpha, forbidden, (x0, y0, x1, y1))
        patch = paper_texture_from_pixels(pixels, crop.size, seed + (index * 97) + 17)
        base = Image.composite(patch, base, soft_full)
        removal = ImageChops.lighter(removal, soft_full)

    out = base.convert("RGBA")
    out.putalpha(alpha)
    return out, removal


def restore_preserved_foreground(base: Image.Image, crop: Image.Image, alpha: Image.Image, box_name: str) -> Image.Image:
    out = base.convert("RGBA")
    for _, rect in PRESERVE_RECTS.get(box_name, []):
        x0, y0, x1, y1 = clamp_rect(rect, crop.size)
        if x1 <= x0 or y1 <= y0:
            continue
        region = crop.crop((x0, y0, x1, y1)).convert("RGBA")
        mask = foreground_mask(region, dilation=5, blur=0.75)
        full_mask = Image.new("L", crop.size, 0)
        full_mask.paste(mask, (x0, y0))
        full_mask = ImageChops.multiply(full_mask, alpha)
        source_layer = Image.new("RGBA", crop.size, (255, 255, 255, 0))
        source_layer.paste(region, (x0, y0))
        out = Image.composite(source_layer, out, full_mask)
    out.putalpha(alpha)
    return out


def remove_order_copy_ghost(base: Image.Image, crop: Image.Image, alpha: Image.Image, seed: int) -> Image.Image:
    if crop.height > 130:
        return base
    sample = crop.crop((34, max(68, crop.height - 46), min(crop.width, 430), crop.height - 6)).convert("RGB")
    pixels = np.asarray(sample, dtype=np.uint8).reshape(-1, 3).astype(np.float32)
    patch = paper_texture_from_pixels(pixels, crop.size, seed + 503)
    mask = Image.new("L", crop.size, 0)
    mask.paste(255, (92, 0, crop.width, min(82, crop.height)))
    mask = ImageChops.multiply(mask.filter(ImageFilter.GaussianBlur(9.5)), alpha)
    cleaned = Image.composite(patch, base.convert("RGB"), mask).convert("RGBA")
    cleaned.putalpha(alpha)
    return cleaned


def remove_order_line_fragments(base: Image.Image, crop: Image.Image, alpha: Image.Image, seed: int) -> Image.Image:
    if crop.width != 523 or crop.height != 146:
        return base
    out = base.convert("RGB")
    for index, rect in enumerate(((0, 58, 34, 94), (497, 58, 523, 94))):
        x0, y0, x1, y1 = rect
        mask = Image.new("L", (x1 - x0, y1 - y0), 255).filter(ImageFilter.GaussianBlur(2.0))
        sample_rect = clamp_rect((x0 - 70, y0 - 34, x1 + 70, y1 + 34), crop.size)
        sample = crop.crop(sample_rect).convert("RGB")
        pixels = clean_pixel_pool(sample).astype(np.float32)
        patch = paper_texture_from_pixels(pixels, crop.size, seed + 701 + (index * 31))
        full_mask = Image.new("L", crop.size, 0)
        full_mask.paste(mask.filter(ImageFilter.GaussianBlur(1.4)), (x0, y0))
        out = Image.composite(patch, out, full_mask)
    cleaned = out.convert("RGBA")
    cleaned.putalpha(alpha)
    return cleaned


def translate_mask(mask: Image.Image, dx: int, dy: int) -> Image.Image:
    width, height = mask.size
    out = Image.new("L", mask.size, 0)
    src_x0 = max(0, -dx)
    src_y0 = max(0, -dy)
    src_x1 = min(width, width - dx)
    src_y1 = min(height, height - dy)
    if src_x1 <= src_x0 or src_y1 <= src_y0:
        return out
    out.paste(mask.crop((src_x0, src_y0, src_x1, src_y1)), (max(0, dx), max(0, dy)))
    return out


def save_shadow_layer(source: Image.Image, box: Box, alpha: Image.Image) -> None:
    _, _, width, height = box.xywh
    expanded_size = (width + (SHADOW_PAD * 2), height + (SHADOW_PAD * 2))
    paper = Image.new("L", expanded_size, 0)
    paper.paste(alpha, (SHADOW_PAD, SHADOW_PAD))

    paper_core = paper.filter(ImageFilter.MaxFilter(3))
    contact = translate_mask(paper_core, 2, 6).filter(ImageFilter.GaussianBlur(8.0))
    drop = translate_mask(paper_core, 11, 16).filter(ImageFilter.GaussianBlur(24.0))
    ambient = translate_mask(paper_core, 4, 12).filter(ImageFilter.GaussianBlur(38.0))

    paper_arr = np.asarray(paper).astype(np.float32) / 255.0
    contact_arr = np.asarray(contact).astype(np.float32) / 255.0
    drop_arr = np.asarray(drop).astype(np.float32) / 255.0
    ambient_arr = np.asarray(ambient).astype(np.float32) / 255.0
    alpha_arr = (contact_arr * 0.15) + (drop_arr * 0.105) + (ambient_arr * 0.045)
    alpha_arr *= 1.0 - np.clip(paper_arr * 1.6, 0.0, 1.0)
    alpha_arr = np.asarray(
        Image.fromarray(np.clip(alpha_arr * 255, 0, 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(3.2)),
    ).astype(np.float32)
    yy, xx = np.mgrid[0 : expanded_size[1], 0 : expanded_size[0]]
    edge_distance = np.minimum.reduce([xx, yy, expanded_size[0] - 1 - xx, expanded_size[1] - 1 - yy])
    canvas_fade = np.clip(edge_distance / 30.0, 0.0, 1.0) ** 1.4
    alpha_arr *= canvas_fade

    rgba = np.zeros((expanded_size[1], expanded_size[0], 4), dtype=np.uint8)
    rgba[:, :, 0] = 66
    rgba[:, :, 1] = 51
    rgba[:, :, 2] = 38
    rgba[:, :, 3] = np.clip(alpha_arr * 0.62, 0, 34).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(OUT / f"{box.name}-shadow.png")


def save_edge_layer(
    crop: Image.Image,
    box: Box,
    alpha: Image.Image,
    removal: Image.Image,
    rects: list[tuple[str, tuple[int, int, int, int]]],
) -> None:
    cleanup = cleanup_edge_removal_mask(crop.size, rects)
    edge_mask = perimeter_overlay_mask(alpha, removal, cleanup)
    rgba = crop.convert("RGBA")
    rgba.putalpha(ImageChops.multiply(edge_mask, alpha))
    arr = np.asarray(rgba).copy()
    transparent = arr[:, :, 3] < 2
    arr[transparent, :3] = 255
    arr[transparent, 3] = 0
    Image.fromarray(arr, "RGBA").save(OUT / f"{box.name}-edge.png")


def clean_background(source: Image.Image, box: Box) -> None:
    _, _, width, height = box.xywh
    sample_patch = stitch_samples(source, BODY_TEXTURE_SAMPLES)
    texture = paper_texture(sample_patch, (width, height), seed=41)
    texture = add_texture_noise(texture, seed=401, low_scale=0.75, fine_scale=0.35)
    texture.save(OUT / f"{box.name}.jpg", quality=96)


def clean_paper(source: Image.Image, box: Box) -> None:
    crop = source.crop(box.xyxy).convert("RGBA")
    seed = (box.xywh[0] * 7) + (box.xywh[1] * 11) + box.xywh[2]
    alpha = plate_alpha_mask(crop.size)
    for _, rect in PRESERVE_RECTS.get(box.name, []):
        x0, y0, x1, y1 = clamp_rect(rect, crop.size)
        if x1 > x0 and y1 > y0:
            alpha.paste(255, (x0, y0, x1, y1))
    base, removal = reconstruct_paper_base(crop, alpha, CLEANUP_RECTS[box.name], seed)
    base = restore_preserved_foreground(base, crop, alpha, box.name)
    if box.name == "paper-order":
        base = remove_order_line_fragments(base, crop, alpha, seed)
    Image.new("RGBA", (crop.width + (SHADOW_PAD * 2), crop.height + (SHADOW_PAD * 2)), (0, 0, 0, 0)).save(
        OUT / f"{box.name}-shadow.png",
    )
    base.save(OUT / f"{box.name}-base.png")
    Image.new("RGBA", crop.size, (255, 255, 255, 0)).save(OUT / f"{box.name}-edge.png")


def locked_baseline_lines() -> list[str]:
    manifest = ROOT / "AGENT_BRIEF.md"
    if manifest.exists():
        lines = manifest.read_text(encoding="utf-8").splitlines()
        try:
            start = lines.index("## Locked Baseline - 2026-06-14")
        except ValueError:
            return LOCKED_BASELINE_FALLBACK
        end = len(lines)
        for index in range(start + 1, len(lines)):
            if lines[index].startswith("## "):
                end = index
                break
        section = lines[start:end]
        while section and section[-1] == "":
            section.pop()
        return section
    return LOCKED_BASELINE_FALLBACK


def write_manifest() -> None:
    lines = [
        "# QR Page 1:1 Rescue Brief",
        "",
        "Source coordinate system: `1086 x 1448` pixels.",
        "",
        *locked_baseline_lines(),
        "",
        "## Strategy",
        "",
        "- Use the exported real Odoo-like header from `workspaces/tirrenia-site/public/assets/tirrenia-header/`; do not replace it with a screenshot.",
        "- Keep normal visible copy as real HTML text using Tirrenia Concept fonts.",
        "- Keep the circular `GRAZIE MILLE / PER LA VISITA` stamp baked into `paper-feedback-base.png` through the preserved foreground region.",
        "- Keep `paper-*-shadow.png` and `paper-*-edge.png` for layer compatibility; the current wide-plate pass carries the visible paper, local background, and natural baked shadow in `paper-*-base.png`.",
        "- Use `paper-mobile-card-base.png` only for the dedicated mobile layout; it is a blank paper strip with icons/text/arrow removed so mobile can compose separate real text and cutout assets.",
        "- Start `paper-*-base.png` from the real golden crop, then cover only fixed text/line/icon cleanup regions with source-sampled paper texture through irregular feathered masks.",
        "- Extract arrows with a blue-ink mask so the circular arrow mark remains intact.",
        "",
        "## Layering",
        "",
        "Within each card/order layer:",
        "",
        "1. compatibility `paper-*-shadow.png`",
        "2. `paper-*-base.png` with paper, baked icons/dividers/stamp, and local background",
        "3. compatibility `paper-*-edge.png`",
        "4. extracted arrows/lines/bell where needed",
        "5. real HTML text",
        "",
        "## Cleanup Rectangles",
        "",
        "Rectangles are `x0,y0,x1,y1`, relative to each paper crop.",
        "",
        "```text",
    ]
    for strip, rects in CLEANUP_RECTS.items():
        lines.append(f"{strip}:")
        for label, rect in rects:
            lines.append(f"  {label:<7} {rect[0]},{rect[1]},{rect[2]},{rect[3]}")
    lines.extend(
        [
            "```",
            "",
            "## Asset Map",
            "",
            "Cutouts are extracted from `source/qr-golden.png`; paper bases use wide source crops, preserved non-text visuals, and local sampled paper patches. Shadow/edge PNGs are compatibility layers in this pass.",
            "",
            "| Asset | x | y | w | h |",
            "| --- | ---: | ---: | ---: | ---: |",
        ],
    )
    for box in [BACKGROUND, *PAPER_STRIPS, *CUTOUTS]:
        x, y, w, h = box.xywh
        lines.append(f"| `{box.name}` | {x} | {y} | {w} | {h} |")
    lines.extend(
        [
            "",
            "Generated paper layer sizes:",
            "",
            "| Prefix | Base/edge size | Shadow size | Shadow inset |",
            "| --- | ---: | ---: | ---: |",
        ],
    )
    for box in PAPER_STRIPS:
        _, _, w, h = box.xywh
        lines.append(
            f"| `{box.name}` | `{w} x {h}` | `{w + (SHADOW_PAD * 2)} x {h + (SHADOW_PAD * 2)}` | `-{SHADOW_PAD}px` |",
        )
    (ROOT / "AGENT_BRIEF.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE).convert("RGB")
    if source.size != (1086, 1448):
        raise SystemExit(f"Unexpected source size: {source.size}")

    clean_background(source, BACKGROUND)
    for box in PAPER_STRIPS:
        clean_paper(source, box)
    for box in CUTOUTS:
        save_cutout(source, box)
    write_manifest()


if __name__ == "__main__":
    main()
