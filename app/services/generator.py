from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw


class ImageGenerator:
    """Pluggable image generator.

    Default implementation renders a placeholder image locally to keep the app
    fully runnable without external API credentials.
    """

    def __init__(self, images_dir: Path) -> None:
        self.images_dir = images_dir
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def generate_image(self, saying_id: int, prompt: str) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"saying_{saying_id}_{timestamp}.png"
        output = self.images_dir / filename

        image = Image.new("RGB", (1024, 1024), color=(242, 240, 234))
        draw = ImageDraw.Draw(image)
        wrapped = self._wrap(prompt[:500], width=52)
        draw.multiline_text((40, 40), wrapped, fill=(24, 24, 24), spacing=6)
        image.save(output, format="PNG")
        return output

    @staticmethod
    def _wrap(text: str, width: int = 60) -> str:
        words = text.split()
        lines: list[str] = []
        current = ""

        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        return "\n".join(lines)
