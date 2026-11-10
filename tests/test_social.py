"""Tests for the social preview image."""

import io

from PIL import Image

from portfolio.social import HEIGHT, WIDTH, card


def test_card_is_a_png_of_the_standard_size() -> None:
    """The preview image is the 1200x630 PNG that social sites expect."""
    image = Image.open(io.BytesIO(card("Ada Lovelace", "Writes the first program.", "example.org")))
    assert image.format == "PNG"
    assert image.size == (WIDTH, HEIGHT)


def test_card_shows_the_given_text() -> None:
    """Different text gives a different image, so the card follows the profile and can't go stale."""
    assert card("Ada Lovelace", "One line.", "example.org") != card("Grace Hopper", "One line.", "example.org")
