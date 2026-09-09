from typing import Optional

from bs4 import Tag


RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def parse_book(book: Tag, category: str) -> Optional[dict]:
    """
    Extract the required fields from a single book card.

    Parameters
    ----------
    book : Tag
        BeautifulSoup <article class="product_pod"> element.

    category : str
        Category associated with the page being scraped.

    Returns
    -------
    dict or None
        Parsed book information, or None if the book cannot be parsed.
    """

    try:
        # -----------------------------
        # Title
        # -----------------------------
        title_element = book.select_one("h3 a")

        if title_element is None:
            raise ValueError("Book title not found")

        title = title_element.get("title", "").strip()

        if not title:
            raise ValueError("Book title is empty")

        # -----------------------------
        # Price
        # -----------------------------
        price_element = book.select_one("p.price_color")

        if price_element is None:
            raise ValueError("Book price not found")

        price_text = price_element.get_text(strip=True)

        # Remove the pound symbol and convert to float.
        price_gbp = float(
            price_text.replace("£", "").replace("Â", "").strip()
        )

        # -----------------------------
        # Star rating
        # -----------------------------
        rating_element = book.select_one("p.star-rating")

        if rating_element is None:
            raise ValueError("Star rating not found")

        rating_classes = rating_element.get("class", [])

        rating_text = next(
            (
                class_name
                for class_name in rating_classes
                if class_name in RATING_MAP
            ),
            None,
        )

        if rating_text is None:
            raise ValueError("Invalid star rating")

        star_rating = rating_text
        rating = RATING_MAP[star_rating]

        # -----------------------------
        # Availability
        # -----------------------------
        availability_element = book.select_one(
            "p.instock.availability"
        )

        if availability_element is None:
            raise ValueError("Availability not found")

        availability = availability_element.get_text(
            " ", strip=True
        )

        # -----------------------------
        # In-stock status
        # -----------------------------
        in_stock = availability.lower().startswith("in stock")

        # -----------------------------
        # Return cleaned record
        # -----------------------------
        return {
            "title": title,
            "price_gbp": price_gbp,
            "star_rating": star_rating,
            "rating": rating,
            "availability": availability,
            "in_stock": in_stock,
            "category": category,
        }

    except (ValueError, TypeError) as error:
        print(f"Skipping malformed book: {error}")
        return None