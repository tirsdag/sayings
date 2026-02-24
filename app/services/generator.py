from __future__ import annotations

import hashlib
import random
import re
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


class ImageGenerator:
    """Pluggable image generator.

    Default implementation generates scene-style artwork from prompt semantics
    without rendering prompt text into the image.
    """

    def __init__(self, images_dir: Path) -> None:
        self.images_dir = images_dir
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def generate_image(self, saying_id: int, prompt: str) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"saying_{saying_id}_{timestamp}.png"
        output = self.images_dir / filename

        seed = int(hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8], 16)
        rng = random.Random(seed)
        tokens = set(re.findall(r"[a-zA-Z0-9]+", prompt.lower()))

        palette = self._select_palette(tokens)
        image = self._make_gradient_background((1024, 1024), palette["bg_top"], palette["bg_bottom"])
        draw = ImageDraw.Draw(image, "RGBA")

        self._draw_atmosphere(draw, rng, tokens, palette)
        self._draw_scene_layers(draw, rng, tokens, palette)
        self._draw_foreground_accents(draw, rng, tokens, palette)

        image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
        image.save(output, format="PNG")
        return output

    @staticmethod
    def _make_gradient_background(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
        width, height = size
        image = Image.new("RGB", size)
        px = image.load()
        for y in range(height):
            t = y / (height - 1)
            r = int(top[0] * (1 - t) + bottom[0] * t)
            g = int(top[1] * (1 - t) + bottom[1] * t)
            b = int(top[2] * (1 - t) + bottom[2] * t)
            for x in range(width):
                px[x, y] = (r, g, b)
        return image

    @staticmethod
    def _select_palette(tokens: set[str]) -> dict[str, tuple[int, int, int]]:
        if {"night", "moon", "dark", "stars", "galaxy"} & tokens:
            return {
                "bg_top": (16, 22, 45),
                "bg_bottom": (42, 58, 97),
                "primary": (231, 215, 162),
                "secondary": (139, 167, 224),
                "accent": (200, 121, 184),
                "ground": (37, 52, 78),
            }
        if {"ocean", "sea", "water", "beach", "coast"} & tokens:
            return {
                "bg_top": (118, 204, 221),
                "bg_bottom": (18, 103, 164),
                "primary": (246, 222, 153),
                "secondary": (189, 233, 243),
                "accent": (255, 147, 79),
                "ground": (22, 68, 112),
            }
        if {"forest", "nature", "botanical", "tree", "leaf", "green"} & tokens:
            return {
                "bg_top": (188, 224, 175),
                "bg_bottom": (76, 140, 95),
                "primary": (237, 236, 207),
                "secondary": (144, 193, 136),
                "accent": (228, 165, 101),
                "ground": (62, 96, 71),
            }
        if {"city", "urban", "street", "building", "neon"} & tokens:
            return {
                "bg_top": (72, 80, 107),
                "bg_bottom": (30, 36, 56),
                "primary": (239, 181, 80),
                "secondary": (119, 155, 209),
                "accent": (241, 117, 138),
                "ground": (25, 29, 44),
            }
        return {
            "bg_top": (246, 223, 175),
            "bg_bottom": (241, 168, 109),
            "primary": (244, 237, 221),
            "secondary": (164, 184, 209),
            "accent": (204, 102, 81),
            "ground": (105, 119, 138),
        }

    @staticmethod
    def _draw_atmosphere(
        draw: ImageDraw.ImageDraw,
        rng: random.Random,
        tokens: set[str],
        palette: dict[str, tuple[int, int, int]],
    ) -> None:
        # Sun/moon
        celestial_color = palette["primary"] + (220,)
        if {"night", "moon", "dark"} & tokens:
            x = rng.randint(120, 860)
            y = rng.randint(90, 250)
            r = rng.randint(55, 90)
            draw.ellipse((x - r, y - r, x + r, y + r), fill=celestial_color)
        else:
            x = rng.randint(120, 860)
            y = rng.randint(120, 340)
            r = rng.randint(80, 150)
            draw.ellipse((x - r, y - r, x + r, y + r), fill=celestial_color)

        # Particles/stars/clouds
        particle_count = 120 if {"night", "moon", "stars"} & tokens else 60
        for _ in range(particle_count):
            px = rng.randint(0, 1023)
            py = rng.randint(0, 560)
            pr = rng.randint(1, 3)
            alpha = rng.randint(100, 220)
            color = palette["secondary"] + (alpha,)
            draw.ellipse((px - pr, py - pr, px + pr, py + pr), fill=color)

    @staticmethod
    def _draw_scene_layers(
        draw: ImageDraw.ImageDraw,
        rng: random.Random,
        tokens: set[str],
        palette: dict[str, tuple[int, int, int]],
    ) -> None:
        if {"city", "urban", "building", "street", "neon"} & tokens:
            # Skyline
            x = 0
            while x < 1024:
                w = rng.randint(40, 120)
                h = rng.randint(180, 500)
                y = 820 - h
                draw.rectangle((x, y, x + w, 900), fill=palette["ground"] + (240,))
                for wx in range(x + 8, x + w - 8, 14):
                    for wy in range(y + 8, min(y + h - 10, 820), 18):
                        if rng.random() < 0.35:
                            c = palette["primary"] + (180,)
                            draw.rectangle((wx, wy, wx + 6, wy + 10), fill=c)
                x += w + rng.randint(8, 18)
        elif {"ocean", "sea", "water", "beach", "coast"} & tokens:
            # Sea bands
            for i in range(7):
                y = 580 + i * 55
                offset = rng.randint(-30, 30)
                draw.polygon(
                    [(0, y + offset), (1024, y - offset), (1024, 1024), (0, 1024)],
                    fill=(palette["ground"][0], palette["ground"][1] + i * 6, palette["ground"][2] + i * 8, 120),
                )
        else:
            # Mountain/hill layers
            for i in range(4):
                base_y = 500 + i * 110
                peak_x = rng.randint(180, 840)
                peak_y = rng.randint(180 + i * 35, 360 + i * 35)
                color = (
                    min(palette["ground"][0] + i * 12, 255),
                    min(palette["ground"][1] + i * 12, 255),
                    min(palette["ground"][2] + i * 12, 255),
                    170,
                )
                draw.polygon([(0, base_y), (peak_x, peak_y), (1024, base_y), (1024, 1024), (0, 1024)], fill=color)

    @staticmethod
    def _draw_foreground_accents(
        draw: ImageDraw.ImageDraw,
        rng: random.Random,
        tokens: set[str],
        palette: dict[str, tuple[int, int, int]],
    ) -> None:
        if {"forest", "nature", "botanical", "tree", "leaf", "green"} & tokens:
            for _ in range(18):
                x = rng.randint(20, 1000)
                trunk_h = rng.randint(80, 180)
                crown_r = rng.randint(28, 56)
                draw.rectangle((x - 5, 880 - trunk_h, x + 5, 900), fill=(72, 54, 36, 220))
                draw.ellipse((x - crown_r, 840 - trunk_h, x + crown_r, 900 - trunk_h), fill=palette["secondary"] + (230,))
        elif {"abstract", "geometric", "minimalist"} & tokens:
            for _ in range(36):
                x1 = rng.randint(0, 900)
                y1 = rng.randint(180, 900)
                x2 = x1 + rng.randint(40, 180)
                y2 = y1 + rng.randint(40, 180)
                color = (palette["accent"][0], palette["accent"][1], palette["accent"][2], rng.randint(70, 140))
                if rng.random() > 0.5:
                    draw.ellipse((x1, y1, x2, y2), fill=color)
                else:
                    draw.rectangle((x1, y1, x2, y2), fill=color)
        else:
            # General accent strokes
            for _ in range(30):
                x = rng.randint(0, 1024)
                y = rng.randint(200, 920)
                length = rng.randint(20, 100)
                width = rng.randint(2, 7)
                color = palette["accent"] + (rng.randint(80, 170),)
                draw.line((x, y, x + length, y + rng.randint(-25, 25)), fill=color, width=width)
