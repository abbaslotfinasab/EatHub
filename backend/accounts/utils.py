from unidecode import unidecode
from django.utils.text import slugify
import uuid


def generate_english_slug(text: str):
    latin = unidecode(text)

    slug = slugify(latin)

    if not slug:
        slug = uuid.uuid4().hex[:8]

    return slug