from collections import OrderedDict

from PIL import Image, ImageOps
import pytesseract
from pytesseract import Output

from ..config import get_settings


def _configure_tesseract() -> None:
    settings = get_settings()
    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


def _prepare_image(image: Image.Image) -> Image.Image:
    grayscale = ImageOps.grayscale(image)
    return ImageOps.autocontrast(grayscale)


def extract_text_from_image(image: Image.Image) -> str:
    _configure_tesseract()
    prepared = _prepare_image(image)
    data = pytesseract.image_to_data(
        prepared,
        output_type=Output.DICT,
        config="--oem 3 --psm 6",
    )

    lines: OrderedDict[tuple[int, int, int, int], list[str]] = OrderedDict()
    total_items = len(data["text"])

    for index in range(total_items):
        word = data["text"][index].strip()
        if not word:
            continue
        key = (
            int(data["page_num"][index]),
            int(data["block_num"][index]),
            int(data["par_num"][index]),
            int(data["line_num"][index]),
        )
        lines.setdefault(key, []).append(word)

    if lines:
        return "\n".join(" ".join(words) for words in lines.values()).strip()

    return pytesseract.image_to_string(prepared, config="--oem 3 --psm 6").strip()
